"""
WearWise Avatar Engine and 3D Geometry Domain Entities
Pure Python dataclasses for meshes, landmarks, shape specs, and shape evaluation results.
"""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional, Any, Set, Tuple
import numpy as np

from app.domain.taxonomies.garment import PresentationGender
from app.domain.exceptions.base import (
    InvalidShapeSpecError,
    InvariantViolationError,
)


@dataclass(frozen=True)
class RegionalShapeScale:
    """Normalized relative scaling intent for an anatomical zone [-1.0, 1.0]."""
    scale_x: float  # Lateral scaling (breadth / width)
    scale_y: float  # Sagittal scaling (depth / protrusion)
    scale_z: float  # Vertical scaling (segment length)

    def __post_init__(self) -> None:
        for axis, val in [("scale_x", self.scale_x), ("scale_y", self.scale_y), ("scale_z", self.scale_z)]:
            if not isinstance(val, (int, float)):
                raise InvalidShapeSpecError(f"Regional scale '{axis}' must be numeric, got {type(val).__name__}")
            if math.isnan(val) or math.isinf(val):
                raise InvalidShapeSpecError(f"Regional scale '{axis}' must be finite, got {val}")
            if not (-1.0 <= float(val) <= 1.0):
                raise InvalidShapeSpecError(f"Regional scale '{axis}' must be in [-1.0, 1.0], got {val}")


@dataclass(frozen=True)
class AvatarShapeSpec:
    """
    Engine-independent specification of avatar shape and stature.
    Input entity consumed by AvatarEngine implementations.
    """
    spec_version: str
    presentation: PresentationGender
    target_stature_cm: float
    target_measurements: Dict[str, float] = field(default_factory=dict)
    regional_scales: Dict[str, RegionalShapeScale] = field(default_factory=dict)
    semantic_controls: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.spec_version or not isinstance(self.spec_version, str):
            raise InvalidShapeSpecError("spec_version must be a non-empty string.")

        if not isinstance(self.presentation, PresentationGender):
            raise InvalidShapeSpecError(f"presentation must be a PresentationGender enum, got {self.presentation}")

        if not isinstance(self.target_stature_cm, (int, float)):
            raise InvalidShapeSpecError("target_stature_cm must be numeric.")
        if math.isnan(self.target_stature_cm) or math.isinf(self.target_stature_cm):
            raise InvalidShapeSpecError("target_stature_cm must be finite.")
        if not (100.0 <= float(self.target_stature_cm) <= 230.0):
            raise InvalidShapeSpecError(
                f"target_stature_cm must be between 100.0 and 230.0 cm, got {self.target_stature_cm}"
            )

        for code, val in self.target_measurements.items():
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val) or val <= 0.0:
                raise InvalidShapeSpecError(
                    f"Target measurement '{code}' must be positive finite, got {val}"
                )

        for ctrl, val in self.semantic_controls.items():
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val) or not (0.0 <= val <= 1.0):
                raise InvalidShapeSpecError(
                    f"Semantic control '{ctrl}' must be in [0.0, 1.0], got {val}"
                )


@dataclass(frozen=True)
class MeshData:
    """
    Engine-independent representation of a 3D surface mesh.
    Vertices are strictly in METERS.
    """
    vertices: np.ndarray           # numpy.ndarray of shape (N, 3), dtype float32, coordinates strictly in METERS
    faces: np.ndarray              # numpy.ndarray of shape (M, 3), dtype int32
    normals: Optional[np.ndarray] = None # numpy.ndarray of shape (N, 3), dtype float32
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.vertices, np.ndarray):
            raise InvariantViolationError("vertices must be a numpy ndarray.")
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise InvariantViolationError(
                f"vertices must have shape (N, 3), got {self.vertices.shape}"
            )
        if self.vertices.shape[0] < 3:
            raise InvariantViolationError(
                f"Mesh must have at least 3 vertices, got {self.vertices.shape[0]}"
            )
        if not np.isfinite(self.vertices).all():
            raise InvariantViolationError("vertices must contain only finite coordinates (no NaN or Inf).")

        if not isinstance(self.faces, np.ndarray):
            raise InvariantViolationError("faces must be a numpy ndarray.")
        if self.faces.ndim != 2 or self.faces.shape[1] != 3:
            raise InvariantViolationError(
                f"faces must have shape (M, 3), got {self.faces.shape}"
            )
        if self.faces.shape[0] < 1:
            raise InvariantViolationError(
                f"Mesh must have at least 1 face, got {self.faces.shape[0]}"
            )


@dataclass(frozen=True)
class LandmarkData:
    """Anatomical landmark coordinates provided by an adapter."""
    landmark_code: str
    point_3d_m: Tuple[float, float, float] # (X, Y, Z) in METERS
    anatomical_region: str

    def __post_init__(self) -> None:
        if not self.landmark_code or not isinstance(self.landmark_code, str):
            raise InvariantViolationError("landmark_code must be a non-empty string.")
        if len(self.point_3d_m) != 3:
            raise InvariantViolationError(f"point_3d_m must have 3 coordinates (X, Y, Z), got {self.point_3d_m}")
        for coord in self.point_3d_m:
            if not isinstance(coord, (int, float)) or math.isnan(coord) or math.isinf(coord):
                raise InvariantViolationError(f"Landmark coordinates must be finite floats, got {self.point_3d_m}")
        if not self.anatomical_region or not isinstance(self.anatomical_region, str):
            raise InvariantViolationError("anatomical_region must be a non-empty string.")


@dataclass(frozen=True)
class RegionalDisplacementSummary:
    """Summary of vertex displacements in a specific anatomical zone in METERS."""
    region_code: str
    mean_displacement_m: float      # Displacement magnitude in METERS
    max_displacement_m: float       # Peak vertex displacement in METERS
    vertex_count: int

    def __post_init__(self) -> None:
        if not self.region_code:
            raise InvariantViolationError("region_code must be a non-empty string.")
        if self.mean_displacement_m < 0.0 or math.isnan(self.mean_displacement_m) or math.isinf(self.mean_displacement_m):
            raise InvariantViolationError("mean_displacement_m must be non-negative finite.")
        if self.max_displacement_m < 0.0 or math.isnan(self.max_displacement_m) or math.isinf(self.max_displacement_m):
            raise InvariantViolationError("max_displacement_m must be non-negative finite.")
        if self.vertex_count < 0:
            raise InvariantViolationError("vertex_count must be non-negative.")


@dataclass(frozen=True)
class ShapeEvaluationResult:
    """
    Geometric feedback returned to BICE for regularized solving.
    RMSR = Regional Mean Spillover Ratio (dimensionless arithmetic ratio).
    PVSR = Peak Vertex Spillover Ratio (dimensionless maximum vertex displacement ratio).
    """
    metric_version: str            # e.g. "1.2.1-rmsr-pvsr"
    evaluation_status: str         # "success", "insufficient_target_signal", "evaluation_failed"
    regional_displacements: Dict[str, RegionalDisplacementSummary]
    target_region_mean_m: float    # Mean target displacement magnitude in METERS
    max_non_target_mean_m: float   # Max non-target regional displacement magnitude in METERS
    rmsr: Optional[float]          # Regional Mean Spillover Ratio (dimensionless); None if insufficient signal
    pvsr: Optional[float]          # Peak Vertex Spillover Ratio (dimensionless); None if insufficient signal
    is_plausible: bool
    diagnostic_notes: str

    def __post_init__(self) -> None:
        if not self.metric_version:
            raise InvariantViolationError("metric_version must be non-empty.")
        if self.evaluation_status not in ("success", "insufficient_target_signal", "evaluation_failed"):
            raise InvariantViolationError(f"Invalid evaluation_status: {self.evaluation_status}")
        if self.target_region_mean_m < 0.0 or not math.isfinite(self.target_region_mean_m):
            raise InvariantViolationError("target_region_mean_m must be non-negative finite.")
        if self.max_non_target_mean_m < 0.0 or not math.isfinite(self.max_non_target_mean_m):
            raise InvariantViolationError("max_non_target_mean_m must be non-negative finite.")
        if self.rmsr is not None:
            if self.rmsr < 0.0 or not math.isfinite(self.rmsr):
                raise InvariantViolationError("rmsr must be non-negative finite when provided.")
        if self.pvsr is not None:
            if self.pvsr < 0.0 or not math.isfinite(self.pvsr):
                raise InvariantViolationError("pvsr must be non-negative finite when provided.")
