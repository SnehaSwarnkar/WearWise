"""
WearWise Anthropometry Engine Package
Canonical geometric intersection, contour stitching, and anthropometric measurement extraction.
"""

from app.anthropometry.models import ContourLoop, ExtractionDiagnostic
from app.anthropometry.engine import (
    AnthropometryEngine,
    ExtractedMeasurementRecord,
    AnthropometryExtractionResult,
    SUPPORTED_CORE_MEASUREMENTS,
)
from app.anthropometry.port import DefaultAnthropometryEvaluationPort
from app.anthropometry.exceptions import (
    AnthropometryError,
    NonManifoldContourError,
    OpenContourError,
    UnclosedContourError,
    SelfIntersectingContourError,
    AmbiguousContourError,
    ImplausiblePerimeterError,
    MissingLandmarkError,
    MeshSliceError,
)
from app.anthropometry.geometry import (
    stitch_segments_into_loops,
    intersect_triangle_with_plane,
    EPSILON_PLANE_M,
    EPSILON_SNAP_M,
    EPSILON_LEN_M,
    AMBIGUITY_MARGIN_M,
)

__all__ = [
    "ContourLoop",
    "ExtractionDiagnostic",
    "AnthropometryError",
    "NonManifoldContourError",
    "OpenContourError",
    "UnclosedContourError",
    "SelfIntersectingContourError",
    "AmbiguousContourError",
    "ImplausiblePerimeterError",
    "MissingLandmarkError",
    "MeshSliceError",
    "stitch_segments_into_loops",
    "intersect_triangle_with_plane",
    "EPSILON_PLANE_M",
    "EPSILON_SNAP_M",
    "EPSILON_LEN_M",
    "AMBIGUITY_MARGIN_M",
    "AnthropometryEngine",
    "ExtractedMeasurementRecord",
    "AnthropometryExtractionResult",
    "DefaultAnthropometryEvaluationPort",
    "SUPPORTED_CORE_MEASUREMENTS",
]
