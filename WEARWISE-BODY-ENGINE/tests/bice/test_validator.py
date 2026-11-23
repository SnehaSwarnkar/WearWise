"""
Test Suite: BICE Validator
Verifies semantic control and anthropometric invariant validation,
including presentation types, stature bounds, measurement integrity,
and anatomical consistency checks.
"""

from decimal import Decimal
import math
import pytest
from app.bice.validator import (
    validate_presentation,
    validate_stature,
    validate_controls_input,
    validate_measurements_input,
)
from app.bice.exceptions import BICEValidationError
from app.domain.entities.body import BodyShapeControls, BodyMeasurement
from app.domain.taxonomies.garment import PresentationGender


def test_validate_presentation_types():
    """Verify presentation accepts both PresentationGender enum and string values, rejecting invalid."""
    assert validate_presentation(PresentationGender.MASCULINE) == PresentationGender.MASCULINE
    assert validate_presentation("feminine") == PresentationGender.FEMININE
    assert validate_presentation("neutral") == PresentationGender.NEUTRAL

    with pytest.raises(BICEValidationError):
        validate_presentation("alien")

    with pytest.raises(BICEValidationError):
        validate_presentation(123)  # type: ignore


def test_validate_stature_edges():
    """Verify validate_stature checks numeric types, non-finite values, and bounds."""
    assert validate_stature(175.5) == 175.5
    assert validate_stature(Decimal("180.0")) == 180.0
    assert validate_stature(100.0) == 100.0
    assert validate_stature(230.0) == 230.0

    with pytest.raises(BICEValidationError):
        validate_stature("175.0")  # type: ignore

    with pytest.raises(BICEValidationError):
        validate_stature(True)  # bool rejected

    with pytest.raises(BICEValidationError):
        validate_stature(float("nan"))

    with pytest.raises(BICEValidationError):
        validate_stature(float("inf"))

    with pytest.raises(BICEValidationError):
        validate_stature(99.9)

    with pytest.raises(BICEValidationError):
        validate_stature(230.1)


def test_validate_controls_input_edges():
    """Verify validate_controls_input rejects invalid container types, non-numeric, non-finite, and out-of-range."""
    with pytest.raises(BICEValidationError):
        validate_controls_input(["not", "a", "dict"])  # type: ignore

    with pytest.raises(BICEValidationError):
        validate_controls_input({"shoulder_width": "wide"})  # type: ignore

    with pytest.raises(BICEValidationError):
        validate_controls_input({"shoulder_width": float("nan")})

    with pytest.raises(BICEValidationError):
        validate_controls_input({"shoulder_width": 0.05})  # min is 0.10


def test_validate_measurements_input_edges():
    """Verify validate_measurements_input validates containers, BodyMeasurement instances, units, and plausibility."""
    with pytest.raises(BICEValidationError):
        validate_measurements_input("invalid_dict")  # type: ignore

    # Valid BodyMeasurement
    bm = BodyMeasurement(measurement_code="stature", value_cm=Decimal("175.0"))
    res = validate_measurements_input({"stature": bm})
    assert res["stature"] == 175.0

    # Non-cm unit on BodyMeasurement (constructed by bypassing post-init or object with unit != 'cm')
    class DummyMeasurement:
        value_cm = 175.0
        unit = "inches"
    with pytest.raises(BICEValidationError):
        validate_measurements_input({"stature": DummyMeasurement()})  # type: ignore

    # Non-numeric measurement value
    with pytest.raises(BICEValidationError):
        validate_measurements_input({"chest_circumference": "large"})  # type: ignore

    # Non-finite or negative measurement
    with pytest.raises(BICEValidationError):
        validate_measurements_input({"chest_circumference": -10.0})

    with pytest.raises(BICEValidationError):
        validate_measurements_input({"chest_circumference": float("nan")})

    # Circumference outside [30.0, 220.0] cm
    with pytest.raises(BICEValidationError):
        validate_measurements_input({"chest_circumference": 25.0})

    with pytest.raises(BICEValidationError):
        validate_measurements_input({"waist_circumference": 230.0})

    # Chest exceeding 150% of stature
    with pytest.raises(BICEValidationError):
        validate_measurements_input({
            "stature": 150.0,
            "chest_circumference": 230.0,  # 230 > 150 * 1.5 (225)
        })
