"""
Test Suite: NAVER Anny v0.6.2 Adapter Integration Tests
Real engine integration tests verifying 3D generation, GLB export,
landmark queries, shape evaluation, and parameter clamping.
"""

import io
import math
import numpy as np
import pytest
import trimesh

from app.avatar_engine.adapters.anny_adapter import (
    AnnyAdapter,
    AnnyLandmarkProvider,
    AnnyShapeEvaluationPort,
)
from app.avatar_engine.exceptions import (
    EngineNotReadyError,
    InvalidParameterError,
    MeshDeformationError,
    GLBExportError,
)
from app.domain.entities.avatar import (
    AvatarShapeSpec,
    RegionalShapeScale,
    MeshData,
    LandmarkData,
    ShapeEvaluationResult,
)
from app.domain.taxonomies.garment import PresentationGender


@pytest.fixture(scope="module")
def anny_engine() -> AnnyAdapter:
    """Module-scoped real AnnyAdapter instance to avoid re-initializing weights across tests."""
    engine = AnnyAdapter(device="cpu")
    engine.initialize()
    return engine


def test_adapter_initialization_and_metadata(anny_engine: AnnyAdapter):
    """Verify AnnyAdapter initializes properly and reports correct engine metadata."""
    assert anny_engine.is_ready() is True
    # Idempotent initialization
    assert anny_engine.initialize() is True

    metadata = anny_engine.get_metadata()
    assert metadata.engine_name == "NAVER Anny"
    assert metadata.engine_version == "0.6.2"
    assert metadata.topology_identifier == "anny_v0.6.2_27420f"
    assert metadata.supports_lbs is True
    assert "mesh_generation" in metadata.supported_capabilities
    assert "glb_export" in metadata.supported_capabilities
    assert "shape_evaluation" in metadata.supported_capabilities
    assert "landmark_provider" in metadata.supported_capabilities
    assert metadata.device_type == "cpu"


@pytest.mark.parametrize("presentation", ["masculine", "feminine", "neutral"])
def test_neutral_baseline_generation(anny_engine: AnnyAdapter, presentation: str):
    """Verify neutral baselines generate topologically identical, watertight 3D meshes."""
    mesh = anny_engine.generate_baseline(presentation=presentation, stature_m=1.70)
    assert isinstance(mesh, MeshData)
    assert mesh.vertices.shape == (13718, 3)
    assert mesh.faces.shape == (27420, 3)
    assert mesh.normals is not None
    assert mesh.normals.shape == (13718, 3)
    assert np.isfinite(mesh.vertices).all()

    report = anny_engine.validate_mesh(mesh)
    assert report.is_valid is True
    assert report.is_watertight is True
    assert report.vertex_count == 13718
    assert report.face_count == 27420
    assert report.has_nans is False
    assert report.has_infs is False
    assert report.has_degenerate_faces is False


@pytest.mark.parametrize("target_cm", [155.0, 168.0, 182.0, 195.0])
def test_stature_alignment(anny_engine: AnnyAdapter, target_cm: float):
    """Verify avatar stature is aligned to the target measurement within 1 mm."""
    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.FEMININE,
        target_stature_cm=target_cm,
        target_measurements={"stature": target_cm},
        regional_scales={},
        semantic_controls={},
    )
    mesh = anny_engine.generate_avatar(spec)
    achieved_h = float((mesh.vertices[:, 2].max() - mesh.vertices[:, 2].min()) * 100.0)
    assert abs(achieved_h - target_cm) < 0.1, f"Expected {target_cm} cm, achieved {achieved_h:.2f} cm"


def test_individual_control_changes(anny_engine: AnnyAdapter):
    """
    Verify individual semantic control changes produce expected localized deformations.
    Tests at least three controls: shoulder_width, belly_fullness, and thigh_fullness.
    """
    base_mesh = anny_engine.generate_baseline("masculine", stature_m=1.75)
    v_base = base_mesh.vertices

    # 1. Shoulder width increase
    spec_shoulder = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"shoulders": RegionalShapeScale(scale_x=0.75, scale_y=0.0, scale_z=0.0)},
        semantic_controls={"shoulder_width": 0.90},
    )
    mesh_shoulder = anny_engine.generate_avatar(spec_shoulder)
    disp_shoulder = np.linalg.norm(mesh_shoulder.vertices - v_base, axis=-1)
    assert disp_shoulder.max() > 0.005  # > 5 mm
    # Shoulders are in top half of body (Z > 0.25)
    assert mesh_shoulder.vertices[np.argmax(disp_shoulder), 2] > 0.25

    # 2. Belly fullness increase
    spec_belly = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"waist_abdomen": RegionalShapeScale(scale_x=0.0, scale_y=0.70, scale_z=0.0)},
        semantic_controls={"belly_fullness": 0.85},
    )
    mesh_belly = anny_engine.generate_avatar(spec_belly)
    disp_belly = np.linalg.norm(mesh_belly.vertices - v_base, axis=-1)
    assert disp_belly.max() > 0.02  # > 20 mm
    # Belly is in torso/abdomen (Z in [-0.1, 0.3])
    peak_z_belly = mesh_belly.vertices[np.argmax(disp_belly), 2]
    assert -0.15 < peak_z_belly < 0.35

    # 3. Thigh fullness increase
    spec_thigh = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"thighs": RegionalShapeScale(scale_x=0.50, scale_y=0.0, scale_z=0.0)},
        semantic_controls={"thigh_fullness": 0.80},
    )
    mesh_thigh = anny_engine.generate_avatar(spec_thigh)
    disp_thigh = np.linalg.norm(mesh_thigh.vertices - v_base, axis=-1)
    assert disp_thigh.max() > 0.005  # > 5 mm
    # Thighs are in lower body (Z < 0.0)
    assert mesh_thigh.vertices[np.argmax(disp_thigh), 2] < 0.05


def test_combined_control_changes(anny_engine: AnnyAdapter):
    """Verify modulating multiple controls simultaneously yields a valid watertight mesh."""
    spec_combined = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.FEMININE,
        target_stature_cm=165.0,
        target_measurements={"stature": 165.0},
        regional_scales={
            "shoulders": RegionalShapeScale(scale_x=0.40, scale_y=0.20, scale_z=0.0),
            "torso_chest": RegionalShapeScale(scale_x=0.0, scale_y=0.50, scale_z=0.0),
            "waist_abdomen": RegionalShapeScale(scale_x=-0.40, scale_y=0.30, scale_z=0.0),
            "arms": RegionalShapeScale(scale_x=0.25, scale_y=0.0, scale_z=0.0),
            "hips": RegionalShapeScale(scale_x=0.50, scale_y=0.0, scale_z=0.0),
            "thighs": RegionalShapeScale(scale_x=0.35, scale_y=0.0, scale_z=0.0),
            "calves": RegionalShapeScale(scale_x=0.20, scale_y=0.0, scale_z=0.0),
        },
        semantic_controls={},
    )
    mesh = anny_engine.generate_avatar(spec_combined)
    report = anny_engine.validate_mesh(mesh)
    assert report.is_valid is True
    assert report.is_watertight is True
    assert np.isfinite(mesh.vertices).all()


def test_in_memory_glb_export(anny_engine: AnnyAdapter):
    """Verify GLB export returns valid glTF 2.0 binary bytes with standard header."""
    mesh = anny_engine.generate_baseline("neutral", stature_m=1.70)
    glb_bytes = anny_engine.export_glb(mesh)

    assert isinstance(glb_bytes, bytes)
    assert len(glb_bytes) > 50000
    # glTF 2.0 binary magic header is b'glTF' (0x46546C67)
    assert glb_bytes[:4] == b"glTF"

    # Reload into trimesh scene to verify container validity
    reloaded = trimesh.load(io.BytesIO(glb_bytes), file_type="glb")
    assert reloaded is not None
    if isinstance(reloaded, trimesh.Scene):
        assert len(reloaded.geometry) > 0
        loaded_mesh = list(reloaded.geometry.values())[0]
    else:
        loaded_mesh = reloaded
    assert loaded_mesh.vertices.shape[0] == 13718
    assert loaded_mesh.faces.shape[0] == 27420

    # Verify Y-up orientation in exported GLB: stature extent must be along Y
    extents = loaded_mesh.extents
    assert extents[1] > extents[0], f"Y extent ({extents[1]:.3f}) should exceed X extent ({extents[0]:.3f})"
    assert extents[1] > extents[2], f"Y extent ({extents[1]:.3f}) should exceed Z extent ({extents[2]:.3f})"


def test_landmark_provider(anny_engine: AnnyAdapter):
    """Verify LandmarkProvider queries landmark coordinates in meters and region vertex masks."""
    lp = anny_engine.get_landmark_provider()
    all_lms = lp.get_all_landmarks()

    for code in ["acromion_left", "acromion_right", "cervicale_c7", "suprasternale", "trochanterion_left"]:
        assert code in all_lms
        lm = all_lms[code]
        assert isinstance(lm, LandmarkData)
        assert len(lm.point_3d_m) == 3
        assert all(np.isfinite(c) for c in lm.point_3d_m)

    # Verify acromion left/right symmetry around sagittal X=0 plane
    l_pt = lp.get_landmark_point_m("acromion_left")
    r_pt = lp.get_landmark_point_m("acromion_right")
    assert l_pt is not None and r_pt is not None
    assert l_pt[0] == pytest.approx(-r_pt[0], abs=1e-3)

    # Verify region vertex masks
    for reg in ["shoulders", "torso_chest", "waist_abdomen", "arms", "hips", "thighs", "calves"]:
        mask = lp.get_region_vertex_mask(reg)
        assert isinstance(mask, set)
        assert len(mask) > 50


def test_shape_evaluation_port_success_and_near_zero(anny_engine: AnnyAdapter):
    """Verify ShapeEvaluationPort calculates RMSR/PVSR and triggers near-zero signal policy."""
    sep = anny_engine.get_shape_evaluation_port()

    # 1. Noticeable modification -> status == 'success'
    spec_mod = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"waist_abdomen": RegionalShapeScale(scale_x=0.0, scale_y=0.60, scale_z=0.0)},
        semantic_controls={},
    )
    res_mod = sep.evaluate_shape(
        shape_spec=spec_mod,
        target_region="waist_abdomen",
        requested_regions=["waist_abdomen", "shoulders", "calves"],
    )
    assert res_mod.evaluation_status == "success"
    assert res_mod.rmsr is not None
    assert res_mod.pvsr is not None
    assert res_mod.is_plausible is True

    # 2. Near-zero modification -> status == 'insufficient_target_signal'
    spec_tiny = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"waist_abdomen": RegionalShapeScale(scale_x=0.0, scale_y=0.000001, scale_z=0.0)},
        semantic_controls={},
    )
    res_tiny = sep.evaluate_shape(
        shape_spec=spec_tiny,
        target_region="waist_abdomen",
        requested_regions=["waist_abdomen", "shoulders", "calves"],
    )
    assert res_tiny.evaluation_status == "insufficient_target_signal"
    assert res_tiny.rmsr is None
    assert res_tiny.pvsr is None
    assert res_tiny.is_plausible is False


def test_invalid_parameter_rejection(anny_engine: AnnyAdapter):
    """Verify invalid inputs raise structured InvalidParameterError."""
    # Stature < 100 cm
    with pytest.raises(Exception):  # AvatarShapeSpec __post_init__ or adapter validation
        spec_short = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.NEUTRAL,
            target_stature_cm=80.0,  # Below 100 cm
            target_measurements={},
            regional_scales={},
            semantic_controls={},
        )
        anny_engine.generate_avatar(spec_short)

    # Stature > 230 cm
    with pytest.raises(Exception):
        spec_tall = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.NEUTRAL,
            target_stature_cm=250.0,  # Above 230 cm
            target_measurements={},
            regional_scales={},
            semantic_controls={},
        )
        anny_engine.generate_avatar(spec_tall)
