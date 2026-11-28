"""
Test Suite: Body Measurement Validation
Verifies units ('cm'), non-negative tolerances, reliability weights in [0.0, 1.0], and positive finite values.
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
from app.domain.exceptions.base import InvalidMeasurementError


def test_valid_measurement():
    """Verify standard valid body measurement."""
    m = BodyMeasurement(
        measurement_code="chest_circumference",
        value_cm=Decimal("104.50"),
        unit="cm",
        acquisition_method=MeasurementAcquisitionMethod.TAPE_MEASURED,
        validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
        lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
        assessment_state=MeasurementAssessmentState.ELIGIBLE,
        tolerance_cm=Decimal("1.00"),
        reliability_weight=Decimal("1.00"),
    )
    assert m.measurement_code == "chest_circumference"
    assert m.value_cm == Decimal("104.50")
    assert m.tolerance_cm == Decimal("1.00")
    assert m.reliability_weight == Decimal("1.00")


def test_invalid_unit():
    """Verify non-'cm' units are rejected."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal("178.0"),
            unit="inches",
        )


@pytest.mark.parametrize("invalid_val", [Decimal("0.0"), Decimal("-10.0"), Decimal("NaN"), Decimal("Infinity")])
def test_invalid_measurement_values(invalid_val):
    """Verify zero, negative, and non-finite values are rejected."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=invalid_val,
        )


@pytest.mark.parametrize("invalid_tol", [Decimal("-0.01"), Decimal("-1.0"), Decimal("NaN")])
def test_negative_tolerance(invalid_tol):
    """Verify negative tolerances are rejected."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="waist_planar_circumference",
            value_cm=Decimal("84.0"),
            tolerance_cm=invalid_tol,
        )


@pytest.mark.parametrize("invalid_rel", [Decimal("-0.1"), Decimal("1.1"), Decimal("2.0"), Decimal("NaN")])
def test_invalid_reliability_weight(invalid_rel):
    """Verify reliability weight must be within [0.0, 1.0]."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="hip_circumference",
            value_cm=Decimal("95.0"),
            reliability_weight=invalid_rel,
        )


def test_empty_measurement_code():
    """Verify empty measurement code is rejected."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="",
            value_cm=Decimal("100.0"),
        )
