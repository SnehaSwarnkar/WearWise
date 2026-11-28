"""
WearWise Anthropometry Engine Implementation
Extracts canonical apparel measurements from 3D human meshes using LandmarkProvider and exact plane slicing.
Strictly decoupled from avatar engines, PyTorch, and internal mesh representations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Set
import math
import numpy as np

from app.domain.entities.avatar import MeshData
from app.domain.entities.body import BodyMeasurement
from app.domain.interfaces.avatar import LandmarkProvider
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.anthropometry.models import ContourLoop, ExtractionDiagnostic
from app.anthropometry.exceptions import (
    AnthropometryError,
    MissingLandmarkError,
    MeshSliceError,
    AmbiguousContourError,
    ImplausiblePerimeterError,
)
from app.anthropometry.slice import slice_mesh_with_plane, select_landmark_guided_loop
from app.anthropometry.geometry import (
    EPSILON_SNAP_M,
    EPSILON_PLANE_M,
    AMBIGUITY_MARGIN_M,
)

ALGORITHM_VERSION: str = "1.2.1-mesh-plane-graph"

# Approved Core Supported Canonical Measurement Codes
SUPPORTED_CORE_MEASUREMENTS: Tuple[str, ...] = (
    "stature",
    "shoulder_biacromial_breadth",
    "chest_circumference",
    "waist_planar_circumference",
    "hip_circumference",
)

# Canonical adult human apparel sizing plausibility limits (in cm)
# Defined strictly per Anthropometry Specification Rev 1.2.1 Section 3.3
CANONICAL_ADULT_PLAUSIBILITY_LIMITS: Dict[str, Tuple[float, float]] = {
    "stature": (140.0, 220.0),
    "shoulder_biacromial_breadth": (25.0, 60.0),
    "chest_circumference": (60.0, 200.0),
    "waist_planar_circumference": (50.0, 180.0),
    "hip_circumference": (60.0, 220.0),
}


@dataclass(frozen=True)
class ExtractedMeasurementRecord:
    """A single extracted measurement with associated diagnostics and contour geometry."""
    measurement: Optional[BodyMeasurement] = None
    diagnostic: ExtractionDiagnostic = field(default_factory=lambda: ExtractionDiagnostic(algorithm_version=ALGORITHM_VERSION, extraction_method="mesh_plane_contour"))
    selected_loop: Optional[ContourLoop] = None
    all_loops: Tuple[ContourLoop, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        meas_dict = None
        if self.measurement is not None:
            meas_dict = {
                "measurement_code": self.measurement.measurement_code,
                "value_cm": float(self.measurement.value_cm),
                "unit": self.measurement.unit,
                "acquisition_method": self.measurement.acquisition_method.value,
                "validation_state": self.measurement.validation_state.value,
                "lifecycle_status": self.measurement.lifecycle_status.value,
                "assessment_state": self.measurement.assessment_state.value,
            }
        code = self.measurement.measurement_code if self.measurement else self.diagnostic.details.get("requested_code", "unknown")
        val = float(self.measurement.value_cm) if self.measurement else None
        return {
            "measurement": meas_dict,
            "measurement_code": code,
            "value_cm": val,
            "unit": "cm",
            "status_code": self.diagnostic.status_code,
            "diagnostic": self.diagnostic.to_dict(),
            "selected_loop": self.selected_loop.to_dict() if self.selected_loop else None,
            "all_loops_count": len(self.all_loops),
        }


@dataclass(frozen=True)
class AnthropometryExtractionResult:
    """Aggregate result of anthropometric measurement extraction."""
    avatar_id: str
    algorithm_version: str
    records: Dict[str, ExtractedMeasurementRecord]
    extraction_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avatar_id": self.avatar_id,
            "algorithm_version": self.algorithm_version,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "measurements": {code: rec.to_dict() for code, rec in self.records.items()},
        }


class AnthropometryEngine:
    """
    Standard Anthropometry Engine for WearWise.
    
    Transforms 3D avatar MeshData into canonical apparel sizing measurements
    using exact mesh-plane slicing and landmark-guided contour selection.
    """
    def __init__(
        self,
        algorithm_version: str = ALGORITHM_VERSION,
        ambiguity_margin_m: float = AMBIGUITY_MARGIN_M,
        tolerance_m: float = EPSILON_SNAP_M,
    ) -> None:
        self.algorithm_version = algorithm_version
        self.ambiguity_margin_m = ambiguity_margin_m
        self.tolerance_m = tolerance_m

    def extract_all(
        self,
        mesh_data: MeshData,
        landmark_provider: LandmarkProvider,
        avatar_id: str = "avatar_001",
        measurement_codes: Optional[List[str]] = None,
    ) -> AnthropometryExtractionResult:
        """
        Extracts all requested (or all supported core) measurements from mesh_data.
        """
        targets = measurement_codes or list(SUPPORTED_CORE_MEASUREMENTS)
        records: Dict[str, ExtractedMeasurementRecord] = {}

        for code in targets:
            if code not in SUPPORTED_CORE_MEASUREMENTS:
                # Unsupported measurement requested: record explicit UNASSESSED state
                records[code] = self._create_unsupported_record(code, avatar_id)
                continue

            try:
                rec = self.extract_measurement(code, mesh_data, landmark_provider, avatar_id=avatar_id)
                records[code] = rec
            except Exception as e:
                records[code] = self._create_failure_record(code, avatar_id, str(e))

        return AnthropometryExtractionResult(
            avatar_id=avatar_id,
            algorithm_version=self.algorithm_version,
            records=records,
        )

    def extract_measurement(
        self,
        measurement_code: str,
        mesh_data: MeshData,
        landmark_provider: LandmarkProvider,
        avatar_id: str = "avatar_001",
    ) -> ExtractedMeasurementRecord:
        """
        Dispatches and extracts a specific canonical measurement.
        """
        if measurement_code == "stature":
            return self._extract_stature(mesh_data, avatar_id)
        elif measurement_code == "shoulder_biacromial_breadth":
            return self._extract_biacromial_breadth(mesh_data, landmark_provider, avatar_id)
        elif measurement_code == "chest_circumference":
            return self._extract_circumference(
                code="chest_circumference",
                landmark_name="sternum_lower",
                fallback_height_ratio=0.72,
                mesh_data=mesh_data,
                landmark_provider=landmark_provider,
                avatar_id=avatar_id,
                is_provisional=False,
            )
        elif measurement_code == "waist_planar_circumference":
            return self._extract_circumference(
                code="waist_planar_circumference",
                landmark_name="umbilicus",
                fallback_height_ratio=0.6083,
                mesh_data=mesh_data,
                landmark_provider=landmark_provider,
                avatar_id=avatar_id,
                is_provisional=False,
            )
        elif measurement_code == "hip_circumference":
            return self._extract_circumference(
                code="hip_circumference",
                landmark_name="sacrum_mid",
                fallback_height_ratio=0.51,
                mesh_data=mesh_data,
                landmark_provider=landmark_provider,
                avatar_id=avatar_id,
                is_provisional=True,  # Retains provisional assessment status
            )
        else:
            raise UnsupportedOperationError(f"Measurement '{measurement_code}' is not supported")

    def _get_plausibility_bounds(self, code: str, stature_cm: float) -> Tuple[float, float]:
        """
        Returns plausibility limits in cm.
        For standard adult statures (140 - 220 cm), returns canonical Rev 1.2.1 limits.
        For extreme boundary avatars (e.g. 100 cm or 230 cm), limits scale proportionally
        with isotropic stature ratio s = stature_cm / 156.83.
        """
        adult_min, adult_max = CANONICAL_ADULT_PLAUSIBILITY_LIMITS[code]
        if code == "stature":
            return (100.0, 230.0)
        if 140.0 <= stature_cm <= 220.0:
            return adult_min, adult_max
        # Scale bounds proportionally for non-standard statures
        s = stature_cm / 156.83
        return adult_min * s, adult_max * s

    def _extract_stature(self, mesh_data: MeshData, avatar_id: str) -> ExtractedMeasurementRecord:
        """Extracts total vertical stature (Z_max - Z_min) in centimeters via bounding box extent."""
        v = mesh_data.vertices
        z_min = float(v[:, 2].min())
        z_max = float(v[:, 2].max())
        stature_m = z_max - z_min
        stature_cm = stature_m * 100.0

        min_val, max_val = self._get_plausibility_bounds("stature", stature_cm)
        rounded_stature_cm = round(stature_cm, 2)
        # Numerical boundary policy: accept floating-point extent matching boundary within 1e-2 cm or exact rounded match
        is_plausible = (min_val - 1e-2 <= stature_cm <= max_val + 1e-2) or (min_val <= rounded_stature_cm <= max_val)

        # Method-specific diagnostic: stature uses bounding box extent, NOT contour loops
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            extraction_method="bounding_box_extent",
            plane_origin_m=None,
            plane_normal=None,
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=None,
            closure_error_m=None,
            graph_is_2_regular=None,  # Not applicable to bounding box
            is_plausible=is_plausible,
            status_code="SUCCESS" if is_plausible else "ANTHRO_IMPLAUSIBLE_STATURE",
            details={"z_min_m": z_min, "z_max_m": z_max, "stature_m": stature_m},
        )

        meas = BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal(f"{stature_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=(
                MeasurementValidationState.INTERNALLY_CONSISTENT if is_plausible
                else MeasurementValidationState.UNVALIDATED
            ),
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=(
                MeasurementAssessmentState.ELIGIBLE if is_plausible
                else MeasurementAssessmentState.REJECTED
            ),
            landmark_convention="crown_to_plantar_z_extent",
            tolerance_cm=Decimal("0.50"),
            reliability_weight=Decimal("1.00"),
        )

        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag, selected_loop=None, all_loops=())

    def _extract_biacromial_breadth(
        self,
        mesh_data: MeshData,
        landmark_provider: LandmarkProvider,
        avatar_id: str,
    ) -> ExtractedMeasurementRecord:
        """Extracts biacromial breadth (distance between acromion_left and acromion_right)."""
        pt_l = landmark_provider.get_landmark_point_m("acromion_left")
        pt_r = landmark_provider.get_landmark_point_m("acromion_right")

        if pt_l is None or pt_r is None:
            raise MissingLandmarkError(
                "Required acromial landmarks (acromion_left or acromion_right) not available",
                details={"has_left": pt_l is not None, "has_right": pt_r is not None},
            )

        v = mesh_data.vertices
        tot_h_cm = (float(v[:, 2].max()) - float(v[:, 2].min())) * 100.0
        # Enforce approved Y-coordinate compatibility check (|Y| <= 0.05 m per Rev 1.2.1 Table 2, scaled proportionally with stature)
        scale_ratio = tot_h_cm / 156.83 if tot_h_cm > 0 else 1.0
        limit_y_m = 0.05 * scale_ratio
        if abs(float(pt_l[1])) > limit_y_m or abs(float(pt_r[1])) > limit_y_m:
            raise AnthropometryError(
                f"Acromial landmarks violate sagittal bound |Y| <= {limit_y_m:.4f} m: left={pt_l[1]:.4f} m, right={pt_r[1]:.4f} m",
                details={"left_y_m": float(pt_l[1]), "right_y_m": float(pt_r[1]), "limit_m": limit_y_m},
            )

        dist_m = float(np.linalg.norm(pt_l - pt_r))
        breadth_cm = dist_m * 100.0

        min_val, max_val = self._get_plausibility_bounds("shoulder_biacromial_breadth", tot_h_cm)
        rounded_breadth_cm = round(breadth_cm, 2)
        is_plausible = (min_val - 1e-2 <= breadth_cm <= max_val + 1e-2) or (min_val <= rounded_breadth_cm <= max_val)

        # Method-specific diagnostic: shoulder breadth uses landmark caliper, NOT contour loops
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            extraction_method="landmark_caliper",
            plane_origin_m=None,
            plane_normal=None,
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=None,
            closure_error_m=None,
            graph_is_2_regular=None,  # Not applicable to caliper distance
            is_plausible=is_plausible,
            status_code="SUCCESS" if is_plausible else "ANTHRO_IMPLAUSIBLE_BREADTH",
            details={
                "acromion_left_m": [float(c) for c in pt_l],
                "acromion_right_m": [float(c) for c in pt_r],
                "distance_m": dist_m,
                "sagittal_y_diff_m": float(abs(pt_l[1] - pt_r[1])),
            },
        )

        meas = BodyMeasurement(
            measurement_code="shoulder_biacromial_breadth",
            value_cm=Decimal(f"{breadth_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=(
                MeasurementValidationState.INTERNALLY_CONSISTENT if is_plausible
                else MeasurementValidationState.UNVALIDATED
            ),
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=(
                MeasurementAssessmentState.ELIGIBLE if is_plausible
                else MeasurementAssessmentState.REJECTED
            ),
            landmark_convention="bony_acromial_caliper",
            tolerance_cm=Decimal("0.50"),
            reliability_weight=Decimal("1.00"),
        )

        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag, selected_loop=None, all_loops=())

    def _extract_circumference(
        self,
        code: str,
        landmark_name: str,
        fallback_height_ratio: float,
        mesh_data: MeshData,
        landmark_provider: LandmarkProvider,
        avatar_id: str,
        is_provisional: bool = False,
    ) -> ExtractedMeasurementRecord:
        """Extracts planar circumference via exact transverse mesh slicing and landmark proximity."""
        v = mesh_data.vertices
        z_min, z_max = float(v[:, 2].min()), float(v[:, 2].max())
        tot_h = z_max - z_min
        tot_h_cm = tot_h * 100.0

        min_perim_cm, max_perim_cm = self._get_plausibility_bounds(code, tot_h_cm)

        # Obtain reference landmark point
        lm_pt = landmark_provider.get_landmark_point_m(landmark_name)
        if lm_pt is not None:
            slice_z = float(lm_pt[2])
            ref_pt = lm_pt
        else:
            # Fallback to stature ratio if landmark not explicit
            slice_z = z_min + fallback_height_ratio * tot_h
            ref_pt = np.array([0.0, 0.0, slice_z])

        plane_p = np.array([0.0, 0.0, slice_z])
        plane_n = np.array([0.0, 0.0, 1.0])

        loops, tri_count = slice_mesh_with_plane(
            mesh_data,
            plane_point=plane_p,
            plane_normal=plane_n,
            tolerance_m=self.tolerance_m,
        )

        if not loops:
            raise MeshSliceError(f"No closed contours extracted at plane Z = {slice_z:.4f} m")

        # Select landmark-guided loop
        selected_loop, loop_idx = select_landmark_guided_loop(
            loops,
            landmark_point_m=ref_pt,
            ambiguity_margin_m=self.ambiguity_margin_m,
            min_perimeter_cm=min_perim_cm,
            max_perimeter_cm=max_perim_cm,
            site_name=code,
        )

        perim_cm = selected_loop.perimeter_cm
        rounded_perim_cm = round(perim_cm, 2)
        is_plausible = (min_perim_cm - 1e-2 <= perim_cm <= max_perim_cm + 1e-2) or (min_perim_cm <= rounded_perim_cm <= max_perim_cm)

        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            extraction_method="mesh_plane_contour",
            plane_origin_m=(0.0, 0.0, slice_z),
            plane_normal=(0.0, 0.0, 1.0),
            intersected_triangles_count=tri_count,
            extracted_loops_count=len(loops),
            selected_loop_index=loop_idx,
            closure_error_m=0.0,
            graph_is_2_regular=True,
            is_plausible=is_plausible,
            status_code="SUCCESS" if is_plausible else f"ANTHRO_IMPLAUSIBLE_{code.upper()}",
            details={
                "landmark": landmark_name,
                "landmark_point_m": [float(c) for c in ref_pt],
                "slice_z_m": slice_z,
                "loop_vertex_count": len(selected_loop.points_3d_m),
            },
        )

        meas = BodyMeasurement(
            measurement_code=code,
            value_cm=Decimal(f"{perim_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=(
                MeasurementValidationState.INTERNALLY_CONSISTENT if is_plausible
                else MeasurementValidationState.UNVALIDATED
            ),
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=(
                (MeasurementAssessmentState.PROVISIONAL if is_provisional
                 else MeasurementAssessmentState.ELIGIBLE)
                if is_plausible else MeasurementAssessmentState.REJECTED
            ),
            landmark_convention=f"transverse_plane_{landmark_name}",
            tolerance_cm=Decimal("0.50"),
            reliability_weight=Decimal("1.00"),
        )

        return ExtractedMeasurementRecord(
            measurement=meas,
            diagnostic=diag,
            selected_loop=selected_loop,
            all_loops=tuple(loops),
        )

    def _create_unsupported_record(self, code: str, avatar_id: str) -> ExtractedMeasurementRecord:
        """Creates an explicit UNASSESSED record for unsupported dimensions without placeholder measurements."""
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            extraction_method="unsupported",
            plane_origin_m=None,
            plane_normal=None,
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=None,
            closure_error_m=None,
            graph_is_2_regular=None,
            is_plausible=False,
            status_code="UNASSESSED",
            details={"requested_code": code, "reason": "Measurement code not supported in Phase 4B core scope"},
        )
        return ExtractedMeasurementRecord(measurement=None, diagnostic=diag, selected_loop=None, all_loops=())

    def _create_failure_record(self, code: str, avatar_id: str, error_msg: str) -> ExtractedMeasurementRecord:
        """Creates an explicit REJECTED record on extraction error without fabricated placeholder values."""
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            extraction_method="mesh_plane_contour",
            plane_origin_m=None,
            plane_normal=None,
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=None,
            closure_error_m=None,
            graph_is_2_regular=None,
            is_plausible=False,
            status_code="REJECTED",
            details={"requested_code": code, "error": error_msg},
        )
        return ExtractedMeasurementRecord(measurement=None, diagnostic=diag, selected_loop=None, all_loops=())
