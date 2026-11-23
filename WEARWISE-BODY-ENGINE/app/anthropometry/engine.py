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

# Site-specific plausible perimeter / length bounds (in cm)
SITE_PLAUSIBILITY_LIMITS: Dict[str, Tuple[float, float]] = {
    "stature": (80.0, 250.0),
    "shoulder_biacromial_breadth": (20.0, 65.0),
    "chest_circumference": (50.0, 200.0),
    "waist_planar_circumference": (40.0, 180.0),
    "hip_circumference": (50.0, 220.0),
}


@dataclass(frozen=True)
class ExtractedMeasurementRecord:
    """A single extracted measurement with associated diagnostics and contour geometry."""
    measurement: BodyMeasurement
    diagnostic: ExtractionDiagnostic
    selected_loop: Optional[ContourLoop] = None
    all_loops: Tuple[ContourLoop, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measurement_code": self.measurement.measurement_code,
            "value_cm": float(self.measurement.value_cm),
            "unit": self.measurement.unit,
            "acquisition_method": self.measurement.acquisition_method.value,
            "validation_state": self.measurement.validation_state.value,
            "lifecycle_status": self.measurement.lifecycle_status.value,
            "assessment_state": self.measurement.assessment_state.value,
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
                min_perim_cm=SITE_PLAUSIBILITY_LIMITS["chest_circumference"][0],
                max_perim_cm=SITE_PLAUSIBILITY_LIMITS["chest_circumference"][1],
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
                min_perim_cm=SITE_PLAUSIBILITY_LIMITS["waist_planar_circumference"][0],
                max_perim_cm=SITE_PLAUSIBILITY_LIMITS["waist_planar_circumference"][1],
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
                min_perim_cm=SITE_PLAUSIBILITY_LIMITS["hip_circumference"][0],
                max_perim_cm=SITE_PLAUSIBILITY_LIMITS["hip_circumference"][1],
                mesh_data=mesh_data,
                landmark_provider=landmark_provider,
                avatar_id=avatar_id,
                is_provisional=True,  # Retains provisional assessment status
            )
        else:
            raise UnsupportedOperationError(f"Measurement '{measurement_code}' is not supported")

    def _extract_stature(self, mesh_data: MeshData, avatar_id: str) -> ExtractedMeasurementRecord:
        """Extracts total vertical stature (Z_max - Z_min) in centimeters."""
        v = mesh_data.vertices
        z_min = float(v[:, 2].min())
        z_max = float(v[:, 2].max())
        stature_m = z_max - z_min
        stature_cm = stature_m * 100.0

        min_val, max_val = SITE_PLAUSIBILITY_LIMITS["stature"]
        is_plausible = min_val <= stature_cm <= max_val

        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            plane_origin_m=(0.0, 0.0, z_min),
            plane_normal=(0.0, 0.0, 1.0),
            intersected_triangles_count=0,
            extracted_loops_count=1,
            selected_loop_index=0,
            closure_error_m=0.0,
            graph_is_2_regular=True,
            is_plausible=is_plausible,
            status_code="SUCCESS" if is_plausible else "ANTHRO_IMPLAUSIBLE_STATURE",
            details={"z_min_m": z_min, "z_max_m": z_max, "stature_m": stature_m},
        )

        meas = BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal(f"{stature_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=MeasurementAssessmentState.ELIGIBLE,
            landmark_convention="crown_to_plantar_z_extent",
            tolerance_cm=Decimal("0.50"),
            reliability_weight=Decimal("1.00"),
        )

        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag)

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

        dist_m = float(np.linalg.norm(pt_l - pt_r))
        breadth_cm = dist_m * 100.0

        min_val, max_val = SITE_PLAUSIBILITY_LIMITS["shoulder_biacromial_breadth"]
        is_plausible = min_val <= breadth_cm <= max_val

        mid_point = (pt_l + pt_r) / 2.0
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            plane_origin_m=(float(mid_point[0]), float(mid_point[1]), float(mid_point[2])),
            plane_normal=(1.0, 0.0, 0.0),
            intersected_triangles_count=0,
            extracted_loops_count=1,
            selected_loop_index=0,
            closure_error_m=0.0,
            graph_is_2_regular=True,
            is_plausible=is_plausible,
            status_code="SUCCESS" if is_plausible else "ANTHRO_IMPLAUSIBLE_BREADTH",
            details={
                "acromion_left_m": list(pt_l),
                "acromion_right_m": list(pt_r),
                "distance_m": dist_m,
            },
        )

        meas = BodyMeasurement(
            measurement_code="shoulder_biacromial_breadth",
            value_cm=Decimal(f"{breadth_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=MeasurementAssessmentState.ELIGIBLE,
            landmark_convention="bony_acromial_caliper",
            tolerance_cm=Decimal("0.50"),
            reliability_weight=Decimal("1.00"),
        )

        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag)

    def _extract_circumference(
        self,
        code: str,
        landmark_name: str,
        fallback_height_ratio: float,
        min_perim_cm: float,
        max_perim_cm: float,
        mesh_data: MeshData,
        landmark_provider: LandmarkProvider,
        avatar_id: str,
        is_provisional: bool = False,
    ) -> ExtractedMeasurementRecord:
        """Extracts planar circumference via exact transverse mesh slicing and landmark proximity."""
        v = mesh_data.vertices
        z_min, z_max = float(v[:, 2].min()), float(v[:, 2].max())
        tot_h = z_max - z_min

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
        is_plausible = min_perim_cm <= perim_cm <= max_perim_cm

        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            plane_origin_m=(0.0, 0.0, slice_z),
            plane_normal=(0.0, 0.0, 1.0),
            intersected_triangles_count=tri_count,
            extracted_loops_count=len(loops),
            selected_loop_index=loop_idx,
            closure_error_m=0.0,
            graph_is_2_regular=True,
            is_plausible=is_plausible,
            status_code="SUCCESS",
            details={
                "landmark": landmark_name,
                "landmark_point_m": list(ref_pt),
                "slice_z_m": slice_z,
                "loop_vertex_count": len(selected_loop.points_3d_m),
            },
        )

        meas = BodyMeasurement(
            measurement_code=code,
            value_cm=Decimal(f"{perim_cm:.2f}"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
            lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
            assessment_state=(
                MeasurementAssessmentState.PROVISIONAL if is_provisional
                else MeasurementAssessmentState.ELIGIBLE
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
        """Creates an explicit UNASSESSED record for unsupported or deferred dimensions."""
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            plane_origin_m=(0.0, 0.0, 0.0),
            plane_normal=(0.0, 0.0, 1.0),
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=-1,
            closure_error_m=0.0,
            graph_is_2_regular=False,
            is_plausible=False,
            status_code="UNASSESSED",
            details={"reason": "Measurement code not supported in Phase 4B core scope"},
        )
        meas = BodyMeasurement(
            measurement_code=code,
            value_cm=Decimal("1.00"),  # placeholder for non-null domain entity
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.MODEL_ESTIMATED,
            validation_state=MeasurementValidationState.UNVALIDATED,
            lifecycle_status=MeasurementLifecycleStatus.DRAFT,
            assessment_state=MeasurementAssessmentState.UNASSESSED,
        )
        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag)

    def _create_failure_record(self, code: str, avatar_id: str, error_msg: str) -> ExtractedMeasurementRecord:
        """Creates an explicit REJECTED record on extraction error (never bounding-box fallback)."""
        diag = ExtractionDiagnostic(
            algorithm_version=self.algorithm_version,
            plane_origin_m=(0.0, 0.0, 0.0),
            plane_normal=(0.0, 0.0, 1.0),
            intersected_triangles_count=0,
            extracted_loops_count=0,
            selected_loop_index=-1,
            closure_error_m=0.0,
            graph_is_2_regular=False,
            is_plausible=False,
            status_code="REJECTED",
            details={"error": error_msg},
        )
        meas = BodyMeasurement(
            measurement_code=code,
            value_cm=Decimal("1.00"),
            unit="cm",
            acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
            validation_state=MeasurementValidationState.DISPUTED,
            lifecycle_status=MeasurementLifecycleStatus.DRAFT,
            assessment_state=MeasurementAssessmentState.REJECTED,
        )
        return ExtractedMeasurementRecord(measurement=meas, diagnostic=diag)
