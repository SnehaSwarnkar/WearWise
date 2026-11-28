"""
Test Suite: Honest Fit Engine Core Functionality
Verifies dimensional ease calculation, 6-tier classification, registry transformations,
effective weighting, evidence coverage 70% gate, and multi-size recommendations.
"""

from decimal import Decimal
import pytest
from uuid import uuid4

from app.domain.entities.body import BodyMeasurement
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import (
    RegionalFitClassification,
    FabricStretchDirection,
)
from app.domain.entities.garment import FabricProperties
from app.fit.rulebook import (
    PROVISIONAL_EASE_INTERVALS,
    MINIMUM_WEARABLE_EASE,
    BASELINE_REGIONAL_WEIGHTS,
    DEFAULT_BETA_COEFFICIENTS,
)
from app.fit.registry import (
    MeasurementCompatibilityRegistry,
    DimensionTransformation,
)
from app.fit.models import (
    GarmentInputSpec,
    FitEvaluationReport,
    GarmentMeasurementProvenance,
)
from app.fit.engine import HonestFitEngine
from app.fit.port import HonestFitEvaluationPort


def make_measurement(code: str, val_cm: float, assessment=MeasurementAssessmentState.ELIGIBLE, validation=MeasurementValidationState.INTERNALLY_CONSISTENT) -> BodyMeasurement:
    return BodyMeasurement(
        measurement_code=code,
        value_cm=Decimal(f"{val_cm:.2f}"),
        unit="cm",
        acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
        validation_state=validation,
        lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
        assessment_state=assessment,
    )


@pytest.fixture
def neutral_masculine_measurements():
    """Real extracted body measurements from NAVER Anny v0.6.2 neutral masculine avatar."""
    return {
        "stature": make_measurement("stature", 156.83, MeasurementAssessmentState.ELIGIBLE),
        "shoulder_biacromial_breadth": make_measurement("shoulder_biacromial_breadth", 37.20, MeasurementAssessmentState.ELIGIBLE),
        "chest_circumference": make_measurement("chest_circumference", 77.85, MeasurementAssessmentState.ELIGIBLE),
        "waist_planar_circumference": make_measurement("waist_planar_circumference", 65.96, MeasurementAssessmentState.ELIGIBLE),
        "hip_circumference": make_measurement("hip_circumference", 91.62, MeasurementAssessmentState.PROVISIONAL),
    }


def test_registry_dimension_transformations():
    """Verify flat width doubling and identity mappings in compatibility registry."""
    # Half width to full circumference
    code, val = MeasurementCompatibilityRegistry.transform_garment_dimension("garment_half_chest_width", 48.5)
    assert code == "chest_circumference"
    assert val == 97.0

    # Half waist to full circumference
    code, val = MeasurementCompatibilityRegistry.transform_garment_dimension("garment_half_waist_width", 42.0)
    assert code == "waist_planar_circumference"
    assert val == 84.0

    # Identity
    code, val = MeasurementCompatibilityRegistry.transform_garment_dimension("garment_chest_circumference", 102.0)
    assert code == "chest_circumference"
    assert val == 102.0

    # Unknown dimension raises KeyError
    with pytest.raises(KeyError):
        MeasurementCompatibilityRegistry.transform_garment_dimension("nonexistent_garment_dimension", 50.0)


def test_registry_deferred_dimensions():
    """Verify deferred dimensions are properly flagged."""
    assert MeasurementCompatibilityRegistry.is_deferred("garment_neck_circumference")
    assert MeasurementCompatibilityRegistry.is_deferred("garment_inseam_length")
    assert MeasurementCompatibilityRegistry.is_deferred("garment_sleeve_length")
    assert not MeasurementCompatibilityRegistry.is_deferred("garment_chest_circumference")


def test_effective_weight_discounting():
    """Verify HFE-001 Section 4.1 effective weighting rules."""
    engine = HonestFitEngine()
    baseline = 0.40

    # 1. ELIGIBLE => 1.0 * baseline
    m_eligible = make_measurement("chest_circumference", 80.0, assessment=MeasurementAssessmentState.ELIGIBLE)
    assert engine.calculate_effective_weight(m_eligible, baseline) == 0.40

    # 2. PROVISIONAL => 0.5 * baseline
    m_provisional = make_measurement("hip_circumference", 90.0, assessment=MeasurementAssessmentState.PROVISIONAL)
    assert engine.calculate_effective_weight(m_provisional, baseline) == 0.20

    # 3. REJECTED => 0.0
    m_rejected = make_measurement("chest_circumference", 50.0, assessment=MeasurementAssessmentState.REJECTED)
    assert engine.calculate_effective_weight(m_rejected, baseline) == 0.0

    # 4. UNASSESSED => 0.0
    m_unassessed = make_measurement("torso_length", 60.0, assessment=MeasurementAssessmentState.UNASSESSED)
    assert engine.calculate_effective_weight(m_unassessed, baseline) == 0.0

    # 5. DISPUTED validation state => 0.0 (overrides ELIGIBLE assessment state)
    m_disputed = make_measurement("chest_circumference", 80.0, assessment=MeasurementAssessmentState.ELIGIBLE, validation=MeasurementValidationState.DISPUTED)
    assert engine.calculate_effective_weight(m_disputed, baseline) == 0.0

    # 6. Missing (None) => 0.0
    assert engine.calculate_effective_weight(None, baseline) == 0.0


def test_evidence_coverage_gate_passed(neutral_masculine_measurements):
    """
    Verify that when chest (0.40) and shoulder (0.30) are available for T-shirt,
    effective weight sum is 0.70 and required denominator is 0.80,
    yielding coverage ratio 0.875 (87.5% >= 70%), passing the gate.
    """
    engine = HonestFitEngine()
    tshirt = GarmentInputSpec(
        title="Basic Crewneck T-Shirt",
        category="t_shirt",
        size_label="M",
        dimensions_cm={
            "garment_chest_circumference": 88.0,
            "garment_shoulder_seam_width": 39.0,
            "garment_back_length": 68.0,
        },
    )
    report = engine.evaluate_fit(neutral_masculine_measurements, tshirt, user_preference="regular")
    assert report.is_coverage_gate_passed is True
    assert report.coverage_ratio == pytest.approx(0.70 / 0.80, abs=1e-4)  # 0.875
    assert report.status == "recommended"
    assert report.composite_score == 100.0  # Perfect regular fit


def test_evidence_coverage_gate_insufficient_data():
    """Verify that if chest is missing, coverage drops below 70% and suppresses scoring."""
    engine = HonestFitEngine()
    # Avatar with only shoulder available
    sparse_measurements = {
        "shoulder_biacromial_breadth": make_measurement("shoulder_biacromial_breadth", 37.20),
    }
    tshirt = GarmentInputSpec(
        title="Basic Crewneck T-Shirt",
        category="t_shirt",
        size_label="M",
        dimensions_cm={
            "garment_chest_circumference": 88.0,
            "garment_shoulder_seam_width": 39.0,
            "garment_back_length": 68.0,
        },
    )
    report = engine.evaluate_fit(sparse_measurements, tshirt, user_preference="regular")
    assert report.is_coverage_gate_passed is False
    assert report.coverage_ratio == pytest.approx(0.30 / 0.80, abs=1e-4)  # 37.5%
    assert report.status == "insufficient_data"
    assert report.composite_score == 0.0
    assert "chest_circumference" in report.missing_required_dimensions
    assert "Insufficient body measurement evidence" in report.summary_explanation


def test_unwearable_rigid_rejection(neutral_masculine_measurements):
    """Verify that non-stretch garment with ease below minimum wearable is rejected as unwearable."""
    engine = HonestFitEngine()
    rigid_cotton = FabricProperties(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.01,
        stretch_recovery_pct=0.85,
        stretch_direction=FabricStretchDirection.RIGID_ZERO,
    )
    # Garment chest 78.0 cm against body chest 77.85 cm => ease +0.15 cm (< +2.0 cm min wearable)
    too_small_tshirt = GarmentInputSpec(
        title="Constricting Tight T-Shirt",
        category="t_shirt",
        size_label="XS",
        dimensions_cm={
            "garment_chest_circumference": 78.0,
            "garment_shoulder_seam_width": 35.0,  # ease -2.2 cm (< -1.0 cm min wearable)
        },
        fabric_properties=rigid_cotton,
    )
    report = engine.evaluate_fit(neutral_masculine_measurements, too_small_tshirt, user_preference="regular")
    assert report.status == "rejected_unwearable"
    assert report.regional_results["chest_circumference"].penalty == 100.0
    assert "rejected as unwearable" in report.summary_explanation


def test_casual_shirt_with_waist_evaluation(neutral_masculine_measurements):
    """Verify casual shirt fit evaluation including chest, waist, and shoulder dimensions."""
    engine = HonestFitEngine()
    shirt = GarmentInputSpec(
        title="Oxford Cloth Button Down Shirt",
        category="casual_shirt",
        size_label="38",
        dimensions_cm={
            "garment_chest_circumference": 88.0,   # ease = 88.0 - 77.85 = +10.15 cm (REGULAR)
            "garment_waist_circumference": 74.0,   # ease = 74.0 - 65.96 = +8.04 cm (REGULAR)
            "garment_shoulder_seam_width": 39.5,  # ease = 39.5 - 37.20 = +2.30 cm (REGULAR)
            "garment_back_length": 72.0,
        },
    )
    report = engine.evaluate_fit(neutral_masculine_measurements, shirt, user_preference="regular")
    assert report.is_coverage_gate_passed is True
    # Denominator: chest 0.40 + shoulders 0.30 + waist 0.20 + length 0.10 = 1.00
    # Available: chest (0.40) + shoulders (0.30) + waist (0.20) = 0.90
    assert report.coverage_ratio == pytest.approx(0.90, abs=1e-4)
    assert report.status == "recommended"
    assert report.composite_score == 100.0
    assert "waist_planar_circumference" in report.regional_results
    assert report.regional_results["waist_planar_circumference"].classification == RegionalFitClassification.REGULAR


def test_multi_size_evaluation_and_ranking(neutral_masculine_measurements):
    """
    Verify ranking across sizes (XS, S, M, L) via HonestFitEvaluationPort.
    Enforces that exactly ONE size is marked 'recommended' (Size S),
    while fitted alternative (XS) and relaxed alternative (M) are consistently 'alternative'.
    """
    port = HonestFitEvaluationPort()

    size_xs = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="XS",
        dimensions_cm={"garment_half_chest_width": 41.5, "garment_shoulder_seam_width": 37.5},
    )
    size_s = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="S",
        dimensions_cm={"garment_half_chest_width": 44.0, "garment_shoulder_seam_width": 39.0},
    )
    size_m = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="M",
        dimensions_cm={"garment_half_chest_width": 47.0, "garment_shoulder_seam_width": 41.5},
    )
    size_l = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="L",
        dimensions_cm={"garment_half_chest_width": 50.5, "garment_shoulder_seam_width": 44.0},
    )

    # For user preferring REGULAR fit:
    # Size S: score 100.0, status RECOMMENDED
    # Size XS: score 91.8, status ALTERNATIVE (fitted alternative to regular)
    # Size M: score 77.0, status ALTERNATIVE (relaxed alternative to regular)
    # Size L: score 0.0, status POOR_FIT
    results = port.evaluate_multi_size_garment(
        neutral_masculine_measurements, [size_l, size_xs, size_s, size_m], user_preference="regular"
    )
    assert len(results) == 4
    assert results[0].size_label == "S"
    assert results[0].status == "recommended"
    assert results[0].composite_score == 100.0

    assert results[1].size_label == "XS"
    assert results[1].status == "alternative"
    assert results[1].composite_score == pytest.approx(91.8, abs=0.1)

    assert results[2].size_label == "M"
    assert results[2].status == "alternative"
    assert results[2].composite_score == pytest.approx(77.0, abs=0.1)

    assert results[3].size_label == "L"
    assert results[3].status == "poor_fit"
    assert results[3].composite_score == 0.0

    # Invariant: exactly one size is recommended
    rec_count = sum(1 for r in results if r.status == "recommended")
    assert rec_count == 1

    best = port.recommend_best_size(
        neutral_masculine_measurements, [size_l, size_xs, size_s, size_m], user_preference="regular"
    )
    assert best is not None
    assert best.size_label == "S"
    assert best.status == "recommended"


def test_single_size_status_consistency(neutral_masculine_measurements):
    """Verify that single-size evaluation marks silhouette deviations as 'alternative' rather than 'recommended'."""
    engine = HonestFitEngine()

    size_xs = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="XS",
        dimensions_cm={"garment_half_chest_width": 41.5, "garment_shoulder_seam_width": 37.5},
    )
    size_s = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="S",
        dimensions_cm={"garment_half_chest_width": 44.0, "garment_shoulder_seam_width": 39.0},
    )

    # 1. Size XS evaluated with 'regular' preference:
    # Has chest ease (+5.15 cm) in fitted and shoulder offset (+0.30 cm) in fitted.
    # Score is 91.8, but status MUST be 'alternative' because it deviates from regular.
    report_xs_reg = engine.evaluate_fit(neutral_masculine_measurements, size_xs, user_preference="regular")
    assert report_xs_reg.status == "alternative"
    assert report_xs_reg.composite_score == pytest.approx(91.8, abs=0.1)

    # 2. Size XS evaluated with 'fitted' preference:
    # Perfectly matches fitted silhouette (zero deviation), so status is 'recommended'.
    report_xs_fit = engine.evaluate_fit(neutral_masculine_measurements, size_xs, user_preference="fitted")
    assert report_xs_fit.status == "recommended"
    assert report_xs_fit.composite_score == 100.0

    # 3. Size S evaluated with 'regular' preference:
    # Perfectly matches regular silhouette (zero deviation), so status is 'recommended'.
    report_s_reg = engine.evaluate_fit(neutral_masculine_measurements, size_s, user_preference="regular")
    assert report_s_reg.status == "recommended"
    assert report_s_reg.composite_score == 100.0


def test_exact_numerical_score_denominator_normalization(neutral_masculine_measurements):
    """
    Verifies that the composite fit score matches the exact worked numerical examples
    with denominator normalization W_eval = sum(w'_j).
    """
    engine = HonestFitEngine()

    # 1. T-Shirt Size XS (Chest w=0.40, Shoulder w=0.30 => Denominator = 0.70)
    # Chest ease +5.15 cm => dev = 6.00 - 5.15 = 0.85 cm => pen = 2.0 * 0.85^2 = 1.445
    # Shoulder ease +0.30 cm => dev = 1.50 - 0.30 = 1.20 cm => pen = 12.0 * 1.20^2 = 17.28
    # Score = 100.0 - (0.40/0.70 * 1.445 + 0.30/0.70 * 17.28)
    #       = 100.0 - (0.8257 + 7.4057) = 91.768
    size_xs = GarmentInputSpec(
        title="T-Shirt", category="t_shirt", size_label="XS",
        dimensions_cm={"garment_half_chest_width": 41.5, "garment_shoulder_seam_width": 37.5},
    )
    report_tshirt = engine.evaluate_fit(neutral_masculine_measurements, size_xs, user_preference="regular")
    expected_tshirt_score = 100.0 - ((0.40 / 0.70) * 1.445 + (0.30 / 0.70) * 17.28)
    assert report_tshirt.composite_score == pytest.approx(expected_tshirt_score, abs=0.01)

    # 2. Casual Shirt Size M (Chest w=0.40, Shoulder w=0.30, Waist w=0.20 => Denominator = 0.90)
    # Chest ease +16.15 cm => dev = 4.15 cm => pen = 2.0 * 4.15^2 = 34.445
    # Waist ease +14.04 cm => dev = 2.04 cm => pen = 2.0 * 2.04^2 = 8.3232
    # Shoulder ease +4.80 cm => dev = 1.30 cm => pen = 12.0 * 1.30^2 = 20.280
    # Score = 100.0 - (0.40/0.90 * 34.445 + 0.30/0.90 * 20.280 + 0.20/0.90 * 8.3232)
    #       = 100.0 - (15.309 + 6.760 + 1.850) = 76.081
    shirt_m = GarmentInputSpec(
        title="Casual Shirt", category="casual_shirt", size_label="M",
        dimensions_cm={
            "garment_chest_circumference": 94.0,
            "garment_waist_circumference": 80.0,
            "garment_shoulder_seam_width": 42.0,
        },
    )
    report_shirt = engine.evaluate_fit(neutral_masculine_measurements, shirt_m, user_preference="regular")
    expected_shirt_score = 100.0 - (
        (0.40 / 0.90) * 34.445 + (0.30 / 0.90) * 20.280 + (0.20 / 0.90) * 8.3232
    )
    assert report_shirt.composite_score == pytest.approx(expected_shirt_score, abs=0.02)


def test_garment_measurement_provenance_and_stretch(neutral_masculine_measurements):
    """Verify provenance metadata serialization and physical mechanical stretch property separation."""
    engine = HonestFitEngine()

    prov = GarmentMeasurementProvenance(
        sample_id="WW-FIXTURE-TSHIRT-2026-001",
        data_origin="demonstration_fixture",
        measuring_instrument="calibrated_rigid_steel_tape_iso_standard",
        measurement_procedure="flat_relaxed_tabletop_bs_4952",
        measurement_date="2026-11-23",
        operator_id="wearwise_qa_lab_1",
        validation_claim="demonstration_fixture_provisional_not_certified",
        notes="Standard reference dimensions for test reproducibility",
    )

    rigid_cotton = FabricProperties(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.015,
        stretch_recovery_pct=0.90,
        stretch_direction=FabricStretchDirection.RIGID_ZERO,
    )

    garment = GarmentInputSpec(
        title="Audited Crewneck Tee",
        category="t_shirt",
        size_label="S",
        dimensions_cm={"garment_half_chest_width": 44.0, "garment_shoulder_seam_width": 39.0},
        fabric_properties=rigid_cotton,
        provenance=prov,
    )

    report = engine.evaluate_fit(neutral_masculine_measurements, garment, user_preference="regular")
    report_dict = report.to_dict()

    # Verify provenance dictionary
    assert report_dict["garment_provenance"] is not None
    assert report_dict["garment_provenance"]["sample_id"] == "WW-FIXTURE-TSHIRT-2026-001"
    assert report_dict["garment_provenance"]["data_origin"] == "demonstration_fixture"
    assert report_dict["garment_provenance"]["validation_claim"] == "demonstration_fixture_provisional_not_certified"

    # Verify fabric properties dictionary decouples stretch from composition
    assert report_dict["fabric_properties"] is not None
    assert report_dict["fabric_properties"]["fibre_composition"] == {"cotton": 1.0}
    assert report_dict["fabric_properties"]["mechanical_stretch_pct"] == 0.015
    assert report_dict["fabric_properties"]["mechanical_stretch_percentage"] == "1.5%"
    assert report_dict["fabric_properties"]["stretch_recovery_percentage"] == "90.0%"
    assert report_dict["fabric_properties"]["testing_standard"] == "BS 4952 / ASTM D3107 (15.0 N load)"
