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
    """Diagnostic metadata for measurement extraction."""
    algorithm_version: str
    plane_origin_m: Tuple[float, float, float]
    plane_normal: Tuple[float, float, float]
    intersected_triangles_count: int
    extracted_loops_count: int
    selected_loop_index: int
    closure_error_m: float
    graph_is_2_regular: bool
    is_plausible: bool
    status_code: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "plane_origin_m": list(self.plane_origin_m),
            "plane_normal": list(self.plane_normal),
            "intersected_triangles_count": self.intersected_triangles_count,
            "extracted_loops_count": self.extracted_loops_count,
            "selected_loop_index": self.selected_loop_index,
            "closure_error_m": float(self.closure_error_m),
            "graph_is_2_regular": self.graph_is_2_regular,
            "is_plausible": self.is_plausible,
            "status_code": self.status_code,
            "details": self.details,
        }
