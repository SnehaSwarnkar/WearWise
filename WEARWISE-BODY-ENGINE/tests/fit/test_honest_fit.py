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
from app.fit.models import GarmentInputSpec, FitEvaluationReport
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
    """Verify ranking across multiple sizes (S, M, L) via HonestFitEvaluationPort."""
    port = HonestFitEvaluationPort()

    size_s = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="S",
        dimensions_cm={"garment_chest_circumference": 88.0, "garment_shoulder_seam_width": 39.0},
    )
    size_m = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="M",
        dimensions_cm={"garment_chest_circumference": 94.0, "garment_shoulder_seam_width": 41.5},
    )
    size_l = GarmentInputSpec(
        title="Everyday Tee", category="t_shirt", size_label="L",
        dimensions_cm={"garment_chest_circumference": 102.0, "garment_shoulder_seam_width": 44.0},
    )

    # For user preferring REGULAR fit:
    # Body: Chest 77.85, Shoulder 37.20
    # Size S: Chest ease +10.15 (REGULAR), Shoulder ease +1.80 (REGULAR) => Perfect 100.0
    # Size M: Chest ease +16.15 (RELAXED), Shoulder ease +4.30 (RELAXED) => Score < 100.0
    # Size L: Chest ease +24.15 (TOO_LARGE), Shoulder ease +6.80 (OVERSIZED) => Score lower
    results = port.evaluate_multi_size_garment(
        neutral_masculine_measurements, [size_l, size_s, size_m], user_preference="regular"
    )
    assert len(results) == 3
    assert results[0].size_label == "S"
    assert results[0].composite_score == 100.0
    assert results[1].size_label == "M"
    assert results[2].size_label == "L"
    assert results[0].composite_score > results[1].composite_score > results[2].composite_score

    best = port.recommend_best_size(
        neutral_masculine_measurements, [size_l, size_s, size_m], user_preference="regular"
    )
    assert best is not None
    assert best.size_label == "S"
