"""
Test Suite: BICE Regional Bounds Engine
Verifies provisional engineering limits, general regional limits,
structured diagnostics generation, non-finite handling, and rejection without silent clamping.
"""

import pytest
from app.bice.bounds import (
    get_regional_axis_bounds,
    check_axis_bound,
    evaluate_regional_bounds,
    validate_regional_bounds,
)
from app.bice.config import (
    PROVISIONAL_REGIONAL_BOUNDS,
    DEFAULT_REGIONAL_BOUNDS,
    BOUNDS_PROVISIONAL_NOTICE,
)
from app.bice.exceptions import BICEBoundsExceededError
from app.domain.entities.avatar import RegionalShapeScale


@pytest.mark.parametrize("region,axes", PROVISIONAL_REGIONAL_BOUNDS.items())
def test_provisional_bounds_exact_acceptance(region, axes):
    """Verify that exact minimum and maximum boundary values are accepted as valid."""
    for axis, (b_min, b_max) in axes.items():
        min_diag = check_axis_bound(region, axis, b_min)
        assert min_diag.is_valid is True
        assert min_diag.violation_amount == 0.0
        assert min_diag.is_provisional is True

        max_diag = check_axis_bound(region, axis, b_max)
        assert max_diag.is_valid is True
        assert max_diag.violation_amount == 0.0
        assert max_diag.is_provisional is True


@pytest.mark.parametrize("region,axes", PROVISIONAL_REGIONAL_BOUNDS.items())
def test_provisional_bounds_rejection(region, axes):
    """Verify values outside provisional bounds are flagged with structured diagnostics."""
    for axis, (b_min, b_max) in axes.items():
        below_diag = check_axis_bound(region, axis, round(b_min - 0.01, 4))
        assert below_diag.is_valid is False
        assert below_diag.violation_amount > 0.0
        assert below_diag.is_provisional is True
        assert "below lower bound" in below_diag.reason

        above_diag = check_axis_bound(region, axis, round(b_max + 0.01, 4))
        assert above_diag.is_valid is False
        assert above_diag.violation_amount > 0.0
        assert above_diag.is_provisional is True
        assert "exceeds upper bound" in above_diag.reason


def test_general_bounds_fallback():
    """Verify non-provisional regions and axes default to [-1.0, 1.0]."""
    b_min, b_max, is_provisional = get_regional_axis_bounds("arms", "scale_x")
    assert b_min == -1.0
    assert b_max == 1.0
    assert is_provisional is False

    valid_diag = check_axis_bound("arms", "scale_x", 0.95)
    assert valid_diag.is_valid is True

    invalid_diag = check_axis_bound("arms", "scale_x", 1.05)
    assert invalid_diag.is_valid is False
    assert invalid_diag.is_provisional is False


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_bounds_check(non_finite):
    """Verify non-finite values are rejected by check_axis_bound."""
    diag = check_axis_bound("thighs", "scale_x", non_finite)
    assert diag.is_valid is False
    assert "cannot be non-finite" in diag.reason


def test_evaluate_regional_bounds_aggregate():
    """Verify aggregate report correctly counts violations and includes provisional notice."""
    scales = {
        "thighs": RegionalShapeScale(scale_x=0.60, scale_y=0.0, scale_z=0.0),  # Violation (max is 0.50)
        "shoulders": RegionalShapeScale(scale_x=-0.80, scale_y=0.0, scale_z=0.0),  # Violation (min is -0.75)
        "arms": RegionalShapeScale(scale_x=0.20, scale_y=0.0, scale_z=0.0),  # Valid
    }
    report = evaluate_regional_bounds(scales)
    assert report.is_valid is False
    assert report.violations_count == 2
    assert report.provisional_notice == BOUNDS_PROVISIONAL_NOTICE

    with pytest.raises(BICEBoundsExceededError):
        validate_regional_bounds(scales, raise_on_error=True)
