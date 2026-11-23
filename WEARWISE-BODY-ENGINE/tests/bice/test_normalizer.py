"""
Test Suite: BICE Semantic Normalizer
Verifies deterministic mapping, neutral 0.50 -> 0.0, strict monotonicity,
safe range boundaries, roundtrip denormalization, and non-finite rejection.
"""

import math
import pytest
from app.bice.normalizer import (
    normalize_control,
    denormalize_control,
    normalize_controls,
    denormalize_controls,
)
from app.bice.config import SEMANTIC_CONTROL_SAFE_RANGES, NEUTRAL_CONTROL_VALUE
from app.bice.exceptions import BICEValidationError
from app.domain.entities.body import BodyShapeControls


@pytest.mark.parametrize("control_name", list(SEMANTIC_CONTROL_SAFE_RANGES.keys()))
def test_neutral_normalization(control_name):
    """Verify neutral 0.50 maps strictly to 0.0 for every control."""
    norm = normalize_control(control_name, 0.50)
    assert norm == 0.0
    denorm = denormalize_control(control_name, 0.0)
    assert denorm == 0.50


@pytest.mark.parametrize("control_name,bounds", SEMANTIC_CONTROL_SAFE_RANGES.items())
def test_exact_boundaries(control_name, bounds):
    """Verify min bound maps to -1.0 and max bound maps to +1.0."""
    min_val, max_val = bounds
    assert normalize_control(control_name, min_val) == -1.0
    assert normalize_control(control_name, max_val) == 1.0

    assert denormalize_control(control_name, -1.0) == min_val
    assert denormalize_control(control_name, 1.0) == max_val


@pytest.mark.parametrize("control_name,bounds", SEMANTIC_CONTROL_SAFE_RANGES.items())
def test_strict_monotonicity(control_name, bounds):
    """Verify that normalize_control is strictly monotonic across the safe range."""
    min_val, max_val = bounds
    steps = 20
    step_size = (max_val - min_val) / steps
    values = [round(min_val + i * step_size, 4) for i in range(steps + 1)]

    normalized_vals = [normalize_control(control_name, v) for v in values]
    for i in range(len(normalized_vals) - 1):
        assert normalized_vals[i] < normalized_vals[i + 1]


@pytest.mark.parametrize("control_name,bounds", SEMANTIC_CONTROL_SAFE_RANGES.items())
def test_out_of_bounds_rejection(control_name, bounds):
    """Verify values just below min and just above max are rejected without clamping."""
    min_val, max_val = bounds
    with pytest.raises(BICEValidationError):
        normalize_control(control_name, round(min_val - 0.01, 4))

    with pytest.raises(BICEValidationError):
        normalize_control(control_name, round(max_val + 0.01, 4))


@pytest.mark.parametrize("control_name", list(SEMANTIC_CONTROL_SAFE_RANGES.keys()))
@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_rejection(control_name, non_finite):
    """Verify NaN and Inf are rejected."""
    with pytest.raises(BICEValidationError):
        normalize_control(control_name, non_finite)

    with pytest.raises(BICEValidationError):
        denormalize_control(control_name, non_finite)


def test_roundtrip_determinism():
    """Verify roundtrip normalization and denormalization recovers input controls."""
    ctrl = BodyShapeControls(
        shoulder_width=0.70,
        chest_fullness=0.30,
        belly_fullness=0.60,
        waist_definition=0.40,
        arm_fullness=0.80,
        hip_fullness=0.65,
        thigh_fullness=0.75,
        calf_fullness=0.55,
    )
    norm = normalize_controls(ctrl)
    recovered = denormalize_controls(norm)
    assert recovered.to_dict() == ctrl.to_dict()


def test_invalid_types():
    """Verify non-numeric values are rejected."""
    with pytest.raises(BICEValidationError):
        normalize_control("shoulder_width", "invalid")  # type: ignore

    with pytest.raises(BICEValidationError):
        normalize_controls("invalid_input")  # type: ignore


@pytest.mark.parametrize("control_name,bounds", SEMANTIC_CONTROL_SAFE_RANGES.items())
def test_float_precision_roundtrip_arbitrary(control_name, bounds):
    """
    Verify that arbitrary valid floating point inputs within safe range
    roundtrip without loss of precision (|c - denorm(norm(c))| < 1e-6).
    """
    min_v, max_v = bounds
    for i in range(51):
        c = min_v + (max_v - min_v) * (i / 50.0)
        norm = normalize_control(control_name, c)
        denorm = denormalize_control(control_name, norm)
        assert abs(c - denorm) < 1e-6
