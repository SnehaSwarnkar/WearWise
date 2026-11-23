"""
Test Suite: AvatarShapeSpec and 3D Geometry Entities Validation
Verifies RegionalShapeScale bounds [-1.0, 1.0], AvatarShapeSpec invariants, MeshData structure, and ShapeEvaluationResult.
"""

import pytest
import numpy as np
from app.domain.entities.avatar import (
    RegionalShapeScale,
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    RegionalDisplacementSummary,
    ShapeEvaluationResult,
)
from app.domain.taxonomies.garment import PresentationGender
from app.domain.exceptions.base import InvalidShapeSpecError, InvariantViolationError


def test_valid_avatar_shape_spec():
    """Verify valid AvatarShapeSpec creation."""
    reg_scales = {
        "shoulders": RegionalShapeScale(scale_x=0.20, scale_y=0.00, scale_z=0.00),
        "chest": RegionalShapeScale(scale_x=0.00, scale_y=0.30, scale_z=0.00),
    }
    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=178.50,
        target_measurements={"chest_circumference": 104.5},
        regional_scales=reg_scales,
        semantic_controls={"shoulder_width": 0.60},
    )
    assert spec.spec_version == "1.2.1"
    assert spec.presentation == PresentationGender.MASCULINE
    assert spec.target_stature_cm == 178.50


@pytest.mark.parametrize("invalid_scale", [-1.05, 1.05, float("nan")])
def test_invalid_regional_scale(invalid_scale):
    """Verify regional scales outside [-1.0, 1.0] are rejected."""
    with pytest.raises(InvalidShapeSpecError):
        RegionalShapeScale(scale_x=invalid_scale, scale_y=0.0, scale_z=0.0)


@pytest.mark.parametrize("invalid_stat", [90.0, 240.0, float("nan")])
def test_invalid_spec_stature(invalid_stat):
    """Verify stature in spec must be in [100.0, 230.0]."""
    with pytest.raises(InvalidShapeSpecError):
        AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.MASCULINE,
            target_stature_cm=invalid_stat,
        )


def test_mesh_data_invariants():
    """Verify MeshData vertex/face structure and NaN rejection."""
    # Valid mesh: 3 vertices in meters, 1 triangular face
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    faces = np.array([[0, 1, 2]], dtype=np.int32)
    mesh = MeshData(vertices=verts, faces=faces)
    assert mesh.vertices.shape == (3, 3)
    assert mesh.faces.shape == (1, 3)

    # Invalid: contains NaN
    verts_nan = verts.copy()
    verts_nan[0, 0] = np.nan
    with pytest.raises(InvariantViolationError):
        MeshData(vertices=verts_nan, faces=faces)

    # Invalid: fewer than 3 vertices
    with pytest.raises(InvariantViolationError):
        MeshData(vertices=verts[:2], faces=faces)


def test_shape_evaluation_result_near_zero():
    """Verify ShapeEvaluationResult handles insufficient_target_signal cleanly."""
    res = ShapeEvaluationResult(
        metric_version="1.2.1-rmsr-pvsr",
        evaluation_status="insufficient_target_signal",
        regional_displacements={},
        target_region_mean_m=0.00005,
        max_non_target_mean_m=0.00001,
        rmsr=None,
        pvsr=None,
        is_plausible=False,
        diagnostic_notes="Target displacement below 0.1 mm threshold.",
    )
    assert res.evaluation_status == "insufficient_target_signal"
    assert res.rmsr is None
    assert res.is_plausible is False
