"""
Test Suite: Domain Interfaces and Protocol Conformance
Verifies that concrete mocks can implement AvatarEngine, ShapeEvaluationPort, LandmarkProvider, and StorageProvider without typing conflicts.
"""

from typing import Optional, Dict, Set, List, Tuple
import numpy as np
import pytest

from app.domain.entities.avatar import (
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    ShapeEvaluationResult,
)
from app.domain.interfaces.avatar import (
    AvatarEngine,
    ShapeEvaluationPort,
    LandmarkProvider,
    MeshValidationReport,
    EngineMetadata,
)
from app.domain.interfaces.storage import StorageProvider
from app.domain.taxonomies.garment import PresentationGender


class MockLandmarkProvider:
    def get_landmark(self, landmark_code: str) -> Optional[LandmarkData]:
        return LandmarkData(landmark_code=landmark_code, point_3d_m=(0.0, 0.0, 0.0), anatomical_region="torso")

    def get_landmark_point_m(self, landmark_code: str) -> Optional[np.ndarray]:
        return np.array([0.0, 0.0, 0.0], dtype=np.float32)

    def get_all_landmarks(self) -> Dict[str, LandmarkData]:
        return {}

    def get_region_vertex_mask(self, region_code: str) -> Set[int]:
        return {0, 1, 2}


class MockShapeEvaluationPort:
    def evaluate_shape(
        self,
        shape_spec: AvatarShapeSpec,
        target_region: str,
        requested_regions: List[str],
    ) -> ShapeEvaluationResult:
        return ShapeEvaluationResult(
            metric_version="1.2.1-rmsr-pvsr",
            evaluation_status="success",
            regional_displacements={},
            target_region_mean_m=0.005,
            max_non_target_mean_m=0.001,
            rmsr=0.20,
            pvsr=0.35,
            is_plausible=True,
            diagnostic_notes="Normal locality signal",
        )


class MockAvatarEngine:
    def initialize(self) -> bool:
        return True

    def is_ready(self) -> bool:
        return True

    def generate_baseline(self, presentation: str, stature_m: float = 1.5683) -> MeshData:
        return MeshData(
            vertices=np.zeros((3, 3), dtype=np.float32),
            faces=np.zeros((1, 3), dtype=np.int32),
        )

    def generate_avatar(self, shape_spec: AvatarShapeSpec) -> MeshData:
        return MeshData(
            vertices=np.zeros((3, 3), dtype=np.float32),
            faces=np.zeros((1, 3), dtype=np.int32),
        )

    def validate_mesh(self, mesh_data: MeshData) -> MeshValidationReport:
        return MeshValidationReport(
            is_valid=True,
            is_watertight=True,
            vertex_count=3,
            face_count=1,
            has_nans=False,
            has_infs=False,
            has_degenerate_faces=False,
            bounding_box_min_m=(0.0, 0.0, 0.0),
            bounding_box_max_m=(1.0, 1.0, 1.0),
        )

    def export_glb(self, mesh_data: MeshData) -> bytes:
        return b"mock_glb_bytes"

    def get_landmark_provider(self) -> LandmarkProvider:
        return MockLandmarkProvider()

    def get_shape_evaluation_port(self) -> ShapeEvaluationPort:
        return MockShapeEvaluationPort()

    def get_metadata(self) -> EngineMetadata:
        return EngineMetadata(
            engine_name="MockEngine",
            engine_version="1.0",
            topology_identifier="mock_topology",
            supports_lbs=True,
            supported_capabilities=["mesh_generation", "glb_export"],
            device_type="cpu",
        )


class MockStorageProvider:
    def store_asset(self, asset_bytes: bytes, content_type: str = "model/gltf-binary") -> Tuple[str, str]:
        return ("/mock/uri.glb", "sha256_mock_hash")

    def retrieve_asset(self, storage_uri: str) -> bytes:
        return b"mock_bytes"

    def delete_asset(self, storage_uri: str) -> bool:
        return True

    def asset_exists(self, storage_uri: str) -> bool:
        return True


def test_interfaces_type_consistency():
    """Verify that mock implementations conform to Protocol definitions without runtime type errors."""
    engine: AvatarEngine = MockAvatarEngine()
    assert engine.initialize() is True
    assert engine.is_ready() is True

    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
    )
    mesh = engine.generate_avatar(spec)
    assert mesh.vertices.shape == (3, 3)

    glb = engine.export_glb(mesh)
    assert glb == b"mock_glb_bytes"

    lp = engine.get_landmark_provider()
    assert isinstance(lp.get_region_vertex_mask("torso"), set)

    sep = engine.get_shape_evaluation_port()
    res = sep.evaluate_shape(spec, "chest", ["shoulders", "waist"])
    assert res.rmsr == 0.20

    storage: StorageProvider = MockStorageProvider()
    uri, digest = storage.store_asset(b"test")
    assert uri == "/mock/uri.glb"
    assert digest == "sha256_mock_hash"
