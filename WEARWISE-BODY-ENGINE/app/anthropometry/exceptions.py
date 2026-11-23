"""
WearWise Anthropometry Exceptions Hierarchy
Domain-compliant exceptions for geometric slicing and contour stitching invariant failures.
"""

from typing import Optional, Dict, Any
from app.domain.exceptions.base import DomainError


class AnthropometryError(DomainError):
    """Base exception for all anthropometric extraction failures."""
    pass


class NonManifoldContourError(AnthropometryError):
    """Raised when the intersection graph has non-manifold edges, branching, or degree > 2."""
    pass


class UnclosedContourError(AnthropometryError):
    """Raised when an extracted segment chain cannot form a closed loop within tolerance."""
    pass


class OpenContourError(UnclosedContourError):
    """Raised when a contour has degree-1 boundary nodes (mesh boundary or hole)."""
    pass


class SelfIntersectingContourError(NonManifoldContourError):
    """Raised when an extracted loop intersects itself (e.g. figure-8 or self-crossing)."""
    pass


class AmbiguousContourError(AnthropometryError):
    """Raised when two or more candidate loops are equidistant to a landmark within the ambiguity margin."""
    pass


class ImplausiblePerimeterError(AnthropometryError):
    """Raised when an extracted loop perimeter falls outside valid anatomical boundaries."""
    pass


class MissingLandmarkError(AnthropometryError):
    """Raised when a required reference landmark is unavailable or missing from LandmarkProvider."""
    pass


class MeshSliceError(AnthropometryError):
    """Raised when mesh-plane slicing fails due to degenerate or empty intersection."""
    pass
