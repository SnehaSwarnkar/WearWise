"""
WearWise Avatar Engine and Shape Evaluation Protocols
Canonical abstract protocols defining the boundaries of 3D generation without engine dependencies.
"""

from typing import Protocol, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import numpy as np

from app.domain.entities.avatar import (
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    ShapeEvaluationResult,
)


@dataclass(frozen=True)
class MeshValidationReport:
    """Structural health and geometric validity report."""
    is_valid: bool
    is_watertight: bool
    vertex_count: int
    face_count: int
    has_nans: bool
    has_infs: bool
    has_degenerate_faces: bool
    bounding_box_min_m: Tuple[float, float, float]
    bounding_box_max_m: Tuple[float, float, float]
    error_message: Optional[str] = None


@dataclass(frozen=True)
class EngineMetadata:
    """Metadata describing the active avatar engine."""
    engine_name: str
    engine_version: str
    topology_identifier: str
    supports_lbs: bool
    supported_capabilities: List[str] # ["mesh_generation", "glb_export", "shape_evaluation", "landmark_provider"]
    device_type: str  # "cpu" or "cuda"


class LandmarkProvider(Protocol):
    """Protocol for querying landmark coordinates and anatomical vertex masks without exposing engine topology."""
    def get_landmark(self, landmark_code: str) -> Optional[LandmarkData]:
        """Returns LandmarkData entity containing 3D coordinates in meters."""
        ...

    def get_landmark_point_m(self, landmark_code: str) -> Optional[np.ndarray]:
        """Returns 3D (X, Y, Z) landmark point as numpy array in METERS in current mesh pose."""
        ...

    def get_all_landmarks(self) -> Dict[str, LandmarkData]:
        """Returns full dictionary of available anatomical landmarks."""
        ...

    def get_region_vertex_mask(self, region_code: str) -> Set[int]:
        """
        Returns the set of mesh vertex indices belonging to the specified anatomical zone.
        During cross-sectional slicing, a triangular face (v0, v1, v2) is included in the slicing
        submesh for region R if at least 2 of its 3 vertices belong to this vertex mask.
        """
        ...


class ShapeEvaluationPort(Protocol):
    """Abstract port for evaluating geometric displacements without importing engine internals."""
    def evaluate_shape(
        self, 
        shape_spec: AvatarShapeSpec, 
        target_region: str, 
        requested_regions: List[str]
    ) -> ShapeEvaluationResult:
        """
        Evaluates regional displacements of candidate shape against reference baseline.
        Returns explicit 'insufficient_target_signal' if target displacement < 10^-4 m.
        """
        ...


class AvatarEngine(Protocol):
    """Abstract interface for all 3D human avatar generation backends."""
    
    def initialize(self) -> bool:
        """Initialize engine weights, neutral templates, and memory buffers. Idempotent."""
        ...
        
    def is_ready(self) -> bool:
        """Return True if engine is ready for forward inference."""
        ...
        
    def generate_baseline(self, presentation: str, stature_m: float = 1.5683) -> MeshData:
        """Generate unedited neutral baseline mesh for a given presentation."""
        ...
        
    def generate_avatar(self, shape_spec: AvatarShapeSpec) -> MeshData:
        """
        Generate customized 3D human mesh from engine-independent AvatarShapeSpec.
        Consumes AvatarShapeSpec; does not accept raw blendshape dictionaries.
        """
        ...
        
    def validate_mesh(self, mesh_data: MeshData) -> MeshValidationReport:
        """Perform topological, manifold, and coordinate bounds checks."""
        ...
        
    def export_glb(self, mesh_data: MeshData) -> bytes:
        """
        Serialize mesh to web-optimized glTF 2.0 binary container.
        Returns raw GLB bytes directly to caller; does not manage storage paths.
        """
        ...
        
    def get_landmark_provider(self, mesh: Optional[MeshData] = None) -> LandmarkProvider:
        """Return neutral landmark query interface for Anthropometry Engine, optionally bound to a specific mesh."""
        ...

    def get_shape_evaluation_port(self) -> ShapeEvaluationPort:
        """Return neutral shape evaluation interface for BICE regularized solver."""
        ...
        
    def get_metadata(self) -> EngineMetadata:
        """Return engine identity and active hardware device info."""
        ...
