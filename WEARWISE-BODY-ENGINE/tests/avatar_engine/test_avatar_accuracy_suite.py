"""
WearWise Phase 13 — Body Engine Anthropometric Accuracy & Shape Differentiation Suite
=====================================================================================
Tests actual Anny avatar mesh generation across heights, genders, body-shape presets,
regional sliders, and multi-target closed-loop measurement calibration.
"""

import io
import pytest
import numpy as np
import trimesh

from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.anthropometry.engine import AnthropometryEngine
from app.bice.mapping import map_controls_to_regional_scales
from app.domain.entities.avatar import AvatarShapeSpec
from app.domain.taxonomies.garment import PresentationGender


@pytest.fixture(scope="module")
def anny_and_engine():
    adapter = AnnyAdapter(device="cpu")
    adapter.initialize()
    engine = AnthropometryEngine()
    return adapter, engine


def _extract(adapter: AnnyAdapter, engine: AnthropometryEngine, md, codes):
    res = engine.extract_all(md, adapter.get_landmark_provider(md), "accuracy_test", tuple(codes))
    out = {}
    for c in codes:
        rec = res.records.get(c)
        out[c] = float(rec.measurement.value_cm) if rec and rec.measurement else None
    return out


def test_masculine_vs_feminine_anatomical_distinction(anny_and_engine):
    """Masculine baseline must show broader chest relative to hips than feminine baseline at equal stature."""
    adapter, engine = anny_and_engine
    m_mesh = adapter.generate_baseline("masculine", stature_m=1.75)
    f_mesh = adapter.generate_baseline("feminine", stature_m=1.75)

    codes = ("chest_circumference", "waist_planar_circumference", "hip_circumference")
    m_vals = _extract(adapter, engine, m_mesh, codes)
    f_vals = _extract(adapter, engine, f_mesh, codes)

    assert m_vals["chest_circumference"] is not None and f_vals["chest_circumference"] is not None
    assert m_vals["hip_circumference"] is not None and f_vals["hip_circumference"] is not None
    # Before fixing inverted gender=0/1, masculine had smaller chest and wider hips than feminine.
    assert m_vals["chest_circumference"] > f_vals["chest_circumference"]
    assert m_vals["hip_circumference"] < f_vals["hip_circumference"]


@pytest.mark.parametrize(
    "label,gender,stature_cm,targets",
    [
        ("slim_male", "masculine", 174.0, {"chest_circumference": 90.0, "waist_planar_circumference": 74.0}),
        ("avg_male", "masculine", 178.0, {"chest_circumference": 98.0, "waist_planar_circumference": 82.0, "hip_circumference": 96.0}),
        ("broad_male", "masculine", 183.0, {"chest_circumference": 110.0, "waist_planar_circumference": 94.0}),
        ("petite_female", "feminine", 158.0, {"chest_circumference": 82.0, "waist_planar_circumference": 66.0, "hip_circumference": 92.0}),
        ("hourglass_female", "feminine", 168.0, {"chest_circumference": 92.0, "waist_planar_circumference": 70.0, "hip_circumference": 100.0}),
        ("curvy_female", "feminine", 170.0, {"chest_circumference": 102.0, "waist_planar_circumference": 84.0, "hip_circumference": 110.0}),
    ],
)
def test_multi_target_body_calibration_accuracy(anny_and_engine, label, gender, stature_cm, targets):
    """Closed-loop Anny calibration must hit realistic stature & chest/waist/hip targets within ~2%."""
    adapter, engine = anny_and_engine
    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender(gender),
        target_stature_cm=stature_cm,
        target_measurements=targets,
        regional_scales={},
        semantic_controls={},
    )
    md = adapter.generate_avatar(spec)
    codes = ("stature",) + tuple(targets.keys())
    measured = _extract(adapter, engine, md, codes)

    assert abs(measured["stature"] - stature_cm) <= 0.5, f"{label}: stature {measured['stature']} != {stature_cm}"
    for code, target_val in targets.items():
        m_val = measured[code]
        assert m_val is not None, f"{label}: missing extracted {code}"
        tol = max(2.2, 0.025 * target_val)
        assert abs(m_val - target_val) <= tol, (
            f"{label}: {code} measured={m_val:.2f} cm vs target={target_val:.2f} cm (tol={tol:.2f})"
        )


def test_slider_presets_produce_meaningful_circumference_deltas(anny_and_engine):
    """Increasing chest/waist/hip/shoulder sliders from 0.25 to 0.85 must visibly shift measurements."""
    adapter, engine = anny_and_engine
    slim_ctrls = {
        "shoulder_width": 0.25,
        "chest_fullness": 0.25,
        "belly_fullness": 0.20,
        "waist_definition": 0.80,
        "arm_fullness": 0.30,
        "hip_fullness": 0.25,
        "thigh_fullness": 0.30,
        "calf_fullness": 0.35,
    }
    broad_ctrls = {
        "shoulder_width": 0.85,
        "chest_fullness": 0.85,
        "belly_fullness": 0.80,
        "waist_definition": 0.20,
        "arm_fullness": 0.80,
        "hip_fullness": 0.85,
        "thigh_fullness": 0.80,
        "calf_fullness": 0.75,
    }

    md_slim = adapter.generate_avatar(
        AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.MASCULINE,
            target_stature_cm=176.0,
            target_measurements={},
            regional_scales=map_controls_to_regional_scales(slim_ctrls),
            semantic_controls=slim_ctrls,
        )
    )
    md_broad = adapter.generate_avatar(
        AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.MASCULINE,
            target_stature_cm=176.0,
            target_measurements={},
            regional_scales=map_controls_to_regional_scales(broad_ctrls),
            semantic_controls=broad_ctrls,
        )
    )
    codes = ("chest_circumference", "waist_planar_circumference", "hip_circumference", "shoulder_biacromial_breadth")
    m_slim = _extract(adapter, engine, md_slim, codes)
    m_broad = _extract(adapter, engine, md_broad, codes)

    assert m_broad["chest_circumference"] - m_slim["chest_circumference"] >= 8.0
    assert m_broad["waist_planar_circumference"] - m_slim["waist_planar_circumference"] >= 8.0
    assert m_broad["hip_circumference"] - m_slim["hip_circumference"] >= 6.0
    assert m_broad["shoulder_biacromial_breadth"] - m_slim["shoulder_biacromial_breadth"] >= 1.0


def test_rigged_glb_centered_and_grounded(anny_and_engine):
    """Exported rigged GLB must sit grounded at y~=0 and center torso around x~=0, z~=0."""
    adapter, _ = anny_and_engine
    md = adapter.generate_baseline("masculine", stature_m=1.78)
    glb = adapter.export_glb(md, rigged=True)
    scene = trimesh.load(io.BytesIO(glb), file_type="glb")
    geom = list(scene.geometry.values())[0] if isinstance(scene, trimesh.Scene) else scene
    v = geom.vertices
    assert abs(float(v[:, 1].min())) < 0.005
    assert abs(float(0.5 * (v[:, 0].min() + v[:, 0].max()))) < 0.02
    h_tot = float(v[:, 1].max() - v[:, 1].min())
    torso = v[(v[:, 1] >= v[:, 1].min() + 0.45 * h_tot) & (v[:, 1] <= v[:, 1].min() + 0.85 * h_tot) & (np.abs(v[:, 0]) < 0.22)]
    assert len(torso) > 50
    torso_z_mid = float(0.5 * (torso[:, 2].min() + torso[:, 2].max()))
    assert abs(torso_z_mid) < 0.02
