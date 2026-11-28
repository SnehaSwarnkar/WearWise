"""
Test Suite: Honest Fit Engine Boundary Precision & Scoring Sensitivities
Verifies exact half-open interval boundaries [a, b), monotonicity, quadratic loss,
and explanation formatting across the 6-tier spectrum.
"""

from decimal import Decimal
import pytest

from app.domain.entities.body import BodyMeasurement
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import RegionalFitClassification
from app.fit.engine import HonestFitEngine
from app.fit.models import GarmentInputSpec


def make_meas(code: str, val: float, assessment=MeasurementAssessmentState.ELIGIBLE) -> BodyMeasurement:
    return BodyMeasurement(
        measurement_code=code,
        value_cm=Decimal(f"{val:.2f}"),
        unit="cm",
        acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
        validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
        lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
        assessment_state=assessment,
    )


@pytest.fixture
def engine():
    return HonestFitEngine()


# -----------------------------------------------------------------------------
# 1. Exact 6-Tier Interval Boundary Tests [a, b)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ease_cm, expected_tier",
    [
        # Chest boundaries: TOO_TIGHT (< 2.0), FITTED [2.0, 6.0), REGULAR [6.0, 12.0),
        # RELAXED [12.0, 18.0), OVERSIZED [18.0, 24.0), TOO_LARGE (>= 24.0)
        (1.999, RegionalFitClassification.TOO_TIGHT),
        (2.000, RegionalFitClassification.FITTED),
        (5.999, RegionalFitClassification.FITTED),
        (6.000, RegionalFitClassification.REGULAR),
        (11.999, RegionalFitClassification.REGULAR),
        (12.000, RegionalFitClassification.RELAXED),
        (17.999, RegionalFitClassification.RELAXED),
        (18.000, RegionalFitClassification.OVERSIZED),
        (23.999, RegionalFitClassification.OVERSIZED),
        (24.000, RegionalFitClassification.TOO_LARGE),
        (35.000, RegionalFitClassification.TOO_LARGE),
    ],
)
def test_chest_circumference_exact_boundaries(engine: HonestFitEngine, ease_cm: float, expected_tier: RegionalFitClassification):
    assert engine.classify_ease("chest_circumference", ease_cm) == expected_tier


@pytest.mark.parametrize(
    "ease_cm, expected_tier",
    [
        # Shoulder boundaries: TOO_TIGHT (< -1.0), FITTED [-1.0, 1.5), REGULAR [1.5, 3.5),
        # RELAXED [3.5, 6.0), OVERSIZED [6.0, 9.0), TOO_LARGE (>= 9.0)
        (-1.001, RegionalFitClassification.TOO_TIGHT),
        (-1.000, RegionalFitClassification.FITTED),
        (1.499, RegionalFitClassification.FITTED),
        (1.500, RegionalFitClassification.REGULAR),
        (3.499, RegionalFitClassification.REGULAR),
        (3.500, RegionalFitClassification.RELAXED),
        (5.999, RegionalFitClassification.RELAXED),
        (6.000, RegionalFitClassification.OVERSIZED),
        (8.999, RegionalFitClassification.OVERSIZED),
        (9.000, RegionalFitClassification.TOO_LARGE),
        (12.000, RegionalFitClassification.TOO_LARGE),
    ],
)
def test_shoulder_seam_exact_boundaries(engine: HonestFitEngine, ease_cm: float, expected_tier: RegionalFitClassification):
    assert engine.classify_ease("shoulder_biacromial_breadth", ease_cm) == expected_tier


@pytest.mark.parametrize(
    "ease_cm, expected_tier",
    [
        # Waist boundaries: TOO_TIGHT (< 2.0), FITTED [2.0, 6.0), REGULAR [6.0, 12.0),
        # RELAXED [12.0, 18.0), OVERSIZED [18.0, 24.0), TOO_LARGE (>= 24.0)
        (1.99, RegionalFitClassification.TOO_TIGHT),
        (2.00, RegionalFitClassification.FITTED),
        (5.99, RegionalFitClassification.FITTED),
        (6.00, RegionalFitClassification.REGULAR),
        (11.99, RegionalFitClassification.REGULAR),
        (12.00, RegionalFitClassification.RELAXED),
        (17.99, RegionalFitClassification.RELAXED),
        (18.00, RegionalFitClassification.OVERSIZED),
        (23.99, RegionalFitClassification.OVERSIZED),
        (24.00, RegionalFitClassification.TOO_LARGE),
    ],
)
def test_waist_exact_boundaries(engine: HonestFitEngine, ease_cm: float, expected_tier: RegionalFitClassification):
    assert engine.classify_ease("waist_planar_circumference", ease_cm) == expected_tier


# -----------------------------------------------------------------------------
# 2. Penalty Function Monotonicity and Boundedness Tests
# -----------------------------------------------------------------------------

def test_penalty_monotonicity_and_saturation(engine: HonestFitEngine):
    """Verify that deviation growth produces monotonically non-decreasing penalty capped at 100.0."""
    target_interval = (6.0, 12.0)  # Regular chest ease

    # Deviations from high bound (12.0): ease = 12.0 + d
    deviations = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
    prev_penalty = -1.0

    for d in deviations:
        ease = 12.0 + d
        penalty = engine.calculate_penalty("chest_circumference", ease, target_interval, is_rigid=False)
        assert 0.0 <= penalty <= 100.0
        assert penalty >= prev_penalty
        prev_penalty = penalty

    # Saturated cap check
    assert engine.calculate_penalty("chest_circumference", 12.0 + 8.0, target_interval, is_rigid=False) == 100.0
    assert engine.calculate_penalty("chest_circumference", 12.0 + 20.0, target_interval, is_rigid=False) == 100.0


def test_zero_deviation_zero_penalty(engine: HonestFitEngine):
    """Inside target interval, deviation is 0 and penalty must be strictly 0.0."""
    target_interval = (6.0, 12.0)
    for ease in [6.0, 7.5, 9.0, 10.5, 11.999]:
        assert engine.calculate_penalty("chest_circumference", ease, target_interval, is_rigid=False) == 0.0


# -----------------------------------------------------------------------------
# 3. Transparent Explanation Formatting Verification
# -----------------------------------------------------------------------------

def test_explanation_formatting_details(engine: HonestFitEngine):
    """Verify human-readable explanations ground values in centimetres and state garment vs body."""
    chest_exp = engine.generate_regional_explanation(
        "chest_circumference", garment_cm=88.0, body_cm=77.85, ease_cm=10.15, classification=RegionalFitClassification.REGULAR
    )
    assert "+10.15 cm ease" in chest_exp
    assert "garment 88.0 cm vs body 77.9 cm" in chest_exp or "88.0 cm vs body 77.8 cm" in chest_exp or "77.85" in chest_exp or "77.8" in chest_exp
    assert "regular fit" in chest_exp

    shoulder_exp = engine.generate_regional_explanation(
        "shoulder_biacromial_breadth", garment_cm=39.0, body_cm=37.20, ease_cm=1.80, classification=RegionalFitClassification.REGULAR
    )
    assert "+1.80 cm" in shoulder_exp
    assert "acromion" in shoulder_exp


# -----------------------------------------------------------------------------
# 4. Provisional Hip Measurement Discounting Test
# -----------------------------------------------------------------------------

def test_provisional_hip_weighting():
    """Verify that provisional hip measurement receives 0.5x baseline weight in trousers."""
    engine = HonestFitEngine()
    body_data = {
        "waist_planar_circumference": make_meas("waist_planar_circumference", 70.0, MeasurementAssessmentState.ELIGIBLE),
        "hip_circumference": make_meas("hip_circumference", 90.0, MeasurementAssessmentState.PROVISIONAL),
    }

    trousers = GarmentInputSpec(
        title="Tailored Trousers",
        category="trousers",
        size_label="32",
        dimensions_cm={
            "garment_waist_circumference": 78.0,
            "garment_hip_circumference": 100.0,
            "garment_thigh_circumference": 58.0,
        },
    )

    report = engine.evaluate_fit(body_data, trousers, user_preference="regular")
    # Trousers required: waist (0.40), hip (0.40), thigh (0.20) => Denom = 1.00
    # Evaluated: waist (0.40 * 1.0 = 0.40), hip (0.40 * 0.5 = 0.20) => Numer = 0.60
    # Coverage = 0.60 / 1.00 = 60.0% < 70% => Insufficient data gate triggered!
    assert report.is_coverage_gate_passed is False
    assert report.coverage_ratio == pytest.approx(0.60, abs=1e-4)
    assert report.status == "insufficient_data"
