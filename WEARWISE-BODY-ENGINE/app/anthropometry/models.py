"""
WearWise Anthropometry Data Contracts and Models
Immutable value objects representing extracted contours and diagnostic metadata.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


@dataclass(frozen=True)
class ContourLoop:
    """An ordered, closed 3D polygonal loop on the mesh surface in METERS."""
    points_3d_m: np.ndarray
    is_closed: bool
    centroid_3d_m: Tuple[float, float, float]
    bounding_box_min_m: Tuple[float, float, float]
    bounding_box_max_m: Tuple[float, float, float]
    perimeter_cm: float

    def __post_init__(self) -> None:
        if not isinstance(self.points_3d_m, np.ndarray):
            object.__setattr__(self, "points_3d_m", np.asarray(self.points_3d_m, dtype=np.float64))
        if self.points_3d_m.ndim != 2 or self.points_3d_m.shape[1] != 3:
            raise ValueError(f"points_3d_m must have shape (K, 3), got {self.points_3d_m.shape}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_closed": self.is_closed,
            "centroid_3d_m": list(self.centroid_3d_m),
            "bounding_box_min_m": list(self.bounding_box_min_m),
            "bounding_box_max_m": list(self.bounding_box_max_m),
            "perimeter_cm": float(self.perimeter_cm),
            "vertex_count": int(len(self.points_3d_m)),
        }


@dataclass(frozen=True)
class ExtractionDiagnostic:
    """Diagnostic metadata for measurement extraction with method-specific semantics."""
    algorithm_version: str
    extraction_method: str  # "mesh_plane_contour", "bounding_box_extent", "landmark_caliper"
    plane_origin_m: Optional[Tuple[float, float, float]] = None
    plane_normal: Optional[Tuple[float, float, float]] = None
    intersected_triangles_count: int = 0
    extracted_loops_count: int = 0
    selected_loop_index: Optional[int] = None
    closure_error_m: Optional[float] = None
    graph_is_2_regular: Optional[bool] = None
    is_plausible: bool = True
    status_code: str = "SUCCESS"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "extraction_method": self.extraction_method,
            "plane_origin_m": list(self.plane_origin_m) if self.plane_origin_m is not None else None,
            "plane_normal": list(self.plane_normal) if self.plane_normal is not None else None,
            "intersected_triangles_count": self.intersected_triangles_count,
            "extracted_loops_count": self.extracted_loops_count,
            "selected_loop_index": self.selected_loop_index,
            "closure_error_m": float(self.closure_error_m) if self.closure_error_m is not None else None,
            "graph_is_2_regular": self.graph_is_2_regular,
            "is_plausible": self.is_plausible,
            "status_code": self.status_code,
            "details": self.details,
        }
