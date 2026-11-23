"""
WearWise Anthropometry Real Anny Integration Test Suite
Verifies extraction against actual NAVER Anny meshes across masculine, feminine,
modified athletic, control variations, extreme stature limits, determinism, and EvaluationPort.
"""

from decimal import Decimal
import numpy as np
import pytest

from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.anthropometry.engine import AnthropometryEngine, SUPPORTED_CORE_MEASUREMENTS
from app.anthropometry.port import DefaultAnthropometryEvaluationPort
from app.domain.entities.avatar import AvatarShapeSpec, RegionalShapeScale
from app.domain.taxonomies.garment import PresentationGender
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementAssessmentState,
)


@pytest.fixture(scope="module")
def anny_engine() -> AnnyAdapter:
    """Provides initialized AnnyAdapter instance for integration tests."""
    adapter = AnnyAdapter(device="cpu")
    adapter.initialize()
    return adapter


@pytest.fixture(scope="module")
def anthro_engine() -> AnthropometryEngine:
    """Provides AnthropometryEngine instance."""
    return AnthropometryEngine()


def test_neutral_masculine_extraction(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies extraction of all 5 canonical core measurements from neutral masculine avatar."""
    mesh = anny_engine.generate_baseline("masculine")
    lp = anny_engine.get_landmark_provider()
    result = anthro_engine.extract_all(mesh, lp, avatar_id="masculine_neutral")

    assert result.avatar_id == "masculine_neutral"
    assert len(result.records) == len(SUPPORTED_CORE_MEASUREMENTS)

    # 1. Stature
    st_rec = result.records["stature"]
    assert st_rec.diagnostic.status_code == "SUCCESS"
    assert st_rec.measurement.value_cm == Decimal("156.83")
    assert st_rec.measurement.assessment_state == MeasurementAssessmentState.ELIGIBLE

    # 2. Shoulder biacromial breadth
    sh_rec = result.records["shoulder_biacromial_breadth"]
    assert sh_rec.diagnostic.status_code == "SUCCESS"
    assert pytest.approx(float(sh_rec.measurement.value_cm), abs=0.5) == 37.20
    assert sh_rec.measurement.assessment_state == MeasurementAssessmentState.ELIGIBLE

    # 3. Chest circumference
    ch_rec = result.records["chest_circumference"]
    assert ch_rec.diagnostic.status_code == "SUCCESS"
    assert pytest.approx(float(ch_rec.measurement.value_cm), abs=1.0) == 77.85
    assert ch_rec.diagnostic.graph_is_2_regular
    assert ch_rec.selected_loop is not None and ch_rec.selected_loop.is_closed

    # 4. Waist planar circumference
    w_rec = result.records["waist_planar_circumference"]
    assert w_rec.diagnostic.status_code == "SUCCESS"
    assert pytest.approx(float(w_rec.measurement.value_cm), abs=1.0) == 65.96
    assert w_rec.diagnostic.graph_is_2_regular

    # 5. Hip circumference (provisional)
    hip_rec = result.records["hip_circumference"]
    assert hip_rec.diagnostic.status_code == "SUCCESS"
    assert pytest.approx(float(hip_rec.measurement.value_cm), abs=1.0) == 91.62
    assert hip_rec.measurement.assessment_state == MeasurementAssessmentState.PROVISIONAL


def test_neutral_feminine_extraction(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies extraction from neutral feminine avatar and anatomical dimorphism."""
    mesh = anny_engine.generate_baseline("feminine")
    lp = anny_engine.get_landmark_provider()
    result = anthro_engine.extract_all(mesh, lp, avatar_id="feminine_neutral")

    assert len(result.records) == len(SUPPORTED_CORE_MEASUREMENTS)
    for code, rec in result.records.items():
        assert rec.diagnostic.status_code == "SUCCESS"
        assert rec.measurement.acquisition_method == MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED
        assert rec.measurement.validation_state == MeasurementValidationState.INTERNALLY_CONSISTENT

    # Feminine dimorphism assertions
    f_sh = float(result.records["shoulder_biacromial_breadth"].measurement.value_cm)
    f_ch = float(result.records["chest_circumference"].measurement.value_cm)
    # Bust circumference is larger in feminine baseline than masculine
    assert f_ch > 80.0
    # Shoulders are narrower than masculine baseline
    assert f_sh < 37.20


def test_modified_athletic_avatar_extraction(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies extraction on modified athletic avatar with custom regional scales."""
    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=180.0,
        target_measurements={"stature": 180.0},
        regional_scales={
            "shoulders": RegionalShapeScale(scale_x=0.45, scale_y=0.0, scale_z=0.0),
            "torso_chest": RegionalShapeScale(scale_x=0.0, scale_y=0.30, scale_z=0.0),
            "waist_abdomen": RegionalShapeScale(scale_x=-0.20, scale_y=-0.20, scale_z=0.0),
        },
        semantic_controls={
            "shoulder_width": 0.85,
            "chest_fullness": 0.75,
            "waist_definition": 0.80,
        },
    )
    mesh = anny_engine.generate_avatar(spec)
    lp = anny_engine.get_landmark_provider()
    result = anthro_engine.extract_all(mesh, lp, avatar_id="modified_athletic")

    st = float(result.records["stature"].measurement.value_cm)
    assert pytest.approx(st, abs=0.1) == 180.0
    sh = float(result.records["shoulder_biacromial_breadth"].measurement.value_cm)
    assert sh > 39.0  # broader shoulders due to shoulder_width control and 180 cm stature


def test_repeated_extraction_determinism(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies that consecutive extractions from the same mesh produce identical numerical values."""
    mesh = anny_engine.generate_baseline("masculine")
    lp = anny_engine.get_landmark_provider()

    run1 = anthro_engine.extract_all(mesh, lp)
    run2 = anthro_engine.extract_all(mesh, lp)

    for code in SUPPORTED_CORE_MEASUREMENTS:
        v1 = run1.records[code].measurement.value_cm
        v2 = run2.records[code].measurement.value_cm
        assert v1 == v2, f"Determinism mismatch for {code}: {v1} != {v2}"

        # If loop exists, check point coordinates
        loop1 = run1.records[code].selected_loop
        loop2 = run2.records[code].selected_loop
        if loop1 is not None and loop2 is not None:
            assert np.allclose(loop1.points_3d_m, loop2.points_3d_m, atol=1e-12)


def test_control_change_sensitivity_belly_and_shoulder(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies that semantic control variations strictly produce expected monotonic measurement changes."""
    def extract_with_scales(waist_sy: float, sh_sx: float):
        spec = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.MASCULINE,
            target_stature_cm=170.0,
            target_measurements={"stature": 170.0},
            regional_scales={
                "waist_abdomen": RegionalShapeScale(scale_x=0.0, scale_y=waist_sy, scale_z=0.0),
                "shoulders": RegionalShapeScale(scale_x=sh_sx, scale_y=0.0, scale_z=0.0),
            },
            semantic_controls={},
        )
        mesh = anny_engine.generate_avatar(spec)
        lp = anny_engine.get_landmark_provider()
        res = anthro_engine.extract_all(mesh, lp)
        return {k: float(rec.measurement.value_cm) for k, rec in res.records.items()}

    base = extract_with_scales(waist_sy=0.0, sh_sx=0.0)
    high_belly = extract_with_scales(waist_sy=0.35, sh_sx=0.0)
    low_belly = extract_with_scales(waist_sy=-0.25, sh_sx=0.0)

    # Waist circumference must strictly increase with waist scale_y
    assert high_belly["waist_planar_circumference"] > base["waist_planar_circumference"]
    assert low_belly["waist_planar_circumference"] <= base["waist_planar_circumference"]

    high_sh = extract_with_scales(waist_sy=0.0, sh_sx=0.35)
    low_sh = extract_with_scales(waist_sy=0.0, sh_sx=-0.25)

    # Shoulder biacromial breadth must strictly increase with shoulder scale_x
    assert high_sh["shoulder_biacromial_breadth"] > base["shoulder_biacromial_breadth"]
    assert low_sh["shoulder_biacromial_breadth"] < base["shoulder_biacromial_breadth"]


def test_stature_limits_100cm_and_230cm(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies extraction at the BICE extreme stature boundaries (100.0 cm and 230.0 cm)."""
    for target_h in [100.0, 230.0]:
        spec = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=PresentationGender.MASCULINE,
            target_stature_cm=target_h,
            target_measurements={"stature": target_h},
            regional_scales={},
            semantic_controls={},
        )
        mesh = anny_engine.generate_avatar(spec)
        lp = anny_engine.get_landmark_provider()
        res = anthro_engine.extract_all(mesh, lp)

        ext_st = float(res.records["stature"].measurement.value_cm)
        assert pytest.approx(ext_st, abs=0.05) == target_h

        # Verify all circumferences are plausible and scaled
        for code in ["chest_circumference", "waist_planar_circumference", "hip_circumference"]:
            assert res.records[code].diagnostic.status_code == "SUCCESS"
            val = float(res.records[code].measurement.value_cm)
            assert val > 30.0


def test_anthropometry_evaluation_port_contract(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies that DefaultAnthropometryEvaluationPort cleanly provides requested dimensions."""
    port = DefaultAnthropometryEvaluationPort(anny_engine, anthro_engine)
    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={},
        semantic_controls={},
    )
    codes = ["stature", "chest_circumference", "waist_planar_circumference"]
    results = port.extract_candidate_measurements(spec, codes)

    assert isinstance(results, dict)
    assert set(results.keys()) == set(codes)
    assert pytest.approx(results["stature"], abs=0.1) == 175.0
    for c in codes:
        assert isinstance(results[c], float)
        assert results[c] > 0.0


def test_unsupported_measurement_handling(anny_engine: AnnyAdapter, anthro_engine: AnthropometryEngine):
    """Verifies that requesting unsupported dimensions records explicit UNASSESSED status (no invented data)."""
    mesh = anny_engine.generate_baseline("masculine")
    lp = anny_engine.get_landmark_provider()
    result = anthro_engine.extract_all(mesh, lp, measurement_codes=["stature", "torso_length", "unsupported_xyz"])

    assert result.records["stature"].diagnostic.status_code == "SUCCESS"
    
    unsupp1 = result.records["torso_length"]
    assert unsupp1.diagnostic.status_code == "UNASSESSED"
    assert unsupp1.measurement.assessment_state == MeasurementAssessmentState.UNASSESSED

    unsupp2 = result.records["unsupported_xyz"]
    assert unsupp2.diagnostic.status_code == "UNASSESSED"
    assert unsupp2.measurement.assessment_state == MeasurementAssessmentState.UNASSESSED
