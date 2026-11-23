"""
Test Suite: Body Shape Controls Validation
Verifies slider range bounds [0.0, 1.0], default values (0.50), and rejection of non-finite values.
"""

import pytest
import math
from app.domain.entities.body import BodyShapeControls
from app.domain.exceptions.base import InvalidControlValueError


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
    """Verify valid control values within [0.0, 1.0]."""
    ctrl = BodyShapeControls(
        shoulder_width=0.10,
        chest_fullness=0.90,
        belly_fullness=0.00,
        waist_definition=1.00,
    )
    assert ctrl.shoulder_width == 0.10
    assert ctrl.chest_fullness == 0.90
    assert ctrl.belly_fullness == 0.00
    assert ctrl.waist_definition == 1.00
    d = ctrl.to_dict()
    assert len(d) == 8
    assert d["shoulder_width"] == 0.10


@pytest.mark.parametrize("invalid_val", [-0.01, 1.01, -1.0, 2.5])
def test_out_of_bounds_controls(invalid_val):
    """Verify values outside [0.0, 1.0] raise InvalidControlValueError."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(shoulder_width=invalid_val)


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_controls(non_finite):
    """Verify NaN and Inf are strictly rejected."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(chest_fullness=non_finite)


def test_non_numeric_control():
    """Verify non-numeric types are rejected."""
    with pytest.raises(InvalidControlValueError):
        BodyShapeControls(belly_fullness="invalid") # type: ignore
