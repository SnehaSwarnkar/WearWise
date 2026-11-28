"""
Test Suite: Body Shape Controls Domain Validation
Verifies control-specific safe ranges, default values (0.50), exact boundary acceptance,
rejection of out-of-range values, and rejection of non-finite values.
"""

import pytest
import math
from app.domain.entities.body import BodyShapeControls, CONTROL_SAFE_RANGES
from app.domain.exceptions.base import InvalidControlValueError


CONTROLS_SAFE_RANGES = [
    ("shoulder_width", 0.10, 0.90),
    ("chest_fullness", 0.10, 0.90),
    ("belly_fullness", 0.10, 0.85),
    ("waist_definition", 0.15, 0.85),
    ("arm_fullness", 0.10, 0.90),
    ("hip_fullness", 0.15, 0.85),
    ("thigh_fullness", 0.20, 0.80),
    ("calf_fullness", 0.15, 0.85),
]


def test_default_controls():
    """Verify neutral defaults are 0.50 across all 8 controls."""
    ctrl = BodyShapeControls()
    assert ctrl.shoulder_width == 0.50
    assert ctrl.chest_fullness == 0.50
    assert ctrl.belly_fullness == 0.50
    assert ctrl.waist_definition == 0.50
    assert ctrl.arm_fullness == 0.50
    assert ctrl.hip_fullness == 0.50
    assert ctrl.thigh_fullness == 0.50
    assert ctrl.calf_fullness == 0.50


def test_valid_custom_controls():
    """Verify valid control values within control-specific safe ranges."""
    ctrl = BodyShapeControls(
        shoulder_width=0.20,
        chest_fullness=0.80,
        belly_fullness=0.30,
        waist_definition=0.70,
    )
    assert ctrl.shoulder_width == 0.20
    assert ctrl.chest_fullness == 0.80
    assert ctrl.belly_fullness == 0.30
    assert ctrl.waist_definition == 0.70
    d = ctrl.to_dict()
    assert len(d) == 8
    assert d["shoulder_width"] == 0.20


@pytest.mark.parametrize("control_name,min_val,max_val", CONTROLS_SAFE_RANGES)
def test_control_minimum_accepted(control_name, min_val, max_val):
    """Verify exact minimum boundary value is accepted."""
    ctrl = BodyShapeControls(**{control_name: min_val})
    assert getattr(ctrl, control_name) == min_val


@pytest.mark.parametrize("control_name,min_val,max_val", CONTROLS_SAFE_RANGES)
def test_control_maximum_accepted(control_name, min_val, max_val):
    """Verify exact maximum boundary value is accepted."""
    ctrl = BodyShapeControls(**{control_name: max_val})
    assert getattr(ctrl, control_name) == max_val


@pytest.mark.parametrize("control_name,min_val,max_val", CONTROLS_SAFE_RANGES)
def test_control_just_below_minimum_rejected(control_name, min_val, max_val):
    """Verify value just below minimum is rejected with InvalidControlValueError."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(**{control_name: round(min_val - 0.01, 4)})


@pytest.mark.parametrize("control_name,min_val,max_val", CONTROLS_SAFE_RANGES)
def test_control_just_above_maximum_rejected(control_name, min_val, max_val):
    """Verify value just above maximum is rejected with InvalidControlValueError."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(**{control_name: round(max_val + 0.01, 4)})


@pytest.mark.parametrize("control_name,min_val,max_val", CONTROLS_SAFE_RANGES)
@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_control_non_finite_rejected(control_name, min_val, max_val, non_finite):
    """Verify NaN and Inf are strictly rejected across all controls."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(**{control_name: non_finite})


def test_non_numeric_control():
    """Verify non-numeric types are rejected."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(belly_fullness="invalid")  # type: ignore
