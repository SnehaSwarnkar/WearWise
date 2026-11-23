"""
WearWise BICE Regional Bounds Engine
Enforces provisional engineering bounds on regional scale axes.
Produces structured diagnostics explaining rejection or status.
Never silently clamps or modifies requested values.
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple
from app.domain.entities.avatar import RegionalShapeScale
from app.bice.config import (
    PROVISIONAL_REGIONAL_BOUNDS,
    DEFAULT_REGIONAL_BOUNDS,
    BOUNDS_PROVISIONAL_NOTICE,
)
from app.bice.exceptions import BICEBoundsExceededError


@dataclass(frozen=True)
class RegionalBoundsDiagnostic:
    """Structured diagnostic record for an individual regional scale axis."""
    region: str
    axis: str
    requested_value: float
    bound_min: float
    bound_max: float
    is_valid: bool
    violation_amount: float
    is_provisional: bool
    reason: Optional[str] = None


@dataclass(frozen=True)
class BoundsCheckReport:
    """Aggregate diagnostic report of regional bounds evaluation."""
    is_valid: bool
    violations_count: int
    diagnostics: List[RegionalBoundsDiagnostic]
    provisional_notice: str
    summary_notes: str


def get_regional_axis_bounds(region: str, axis: str) -> Tuple[float, float, bool]:
    """
    Returns (bound_min, bound_max, is_provisional) for a given region and scale axis.
    """
    if region in PROVISIONAL_REGIONAL_BOUNDS and axis in PROVISIONAL_REGIONAL_BOUNDS[region]:
        b_min, b_max = PROVISIONAL_REGIONAL_BOUNDS[region][axis]
        return b_min, b_max, True

    b_min, b_max = DEFAULT_REGIONAL_BOUNDS
    return b_min, b_max, False


def check_axis_bound(region: str, axis: str, value: float) -> RegionalBoundsDiagnostic:
    """
    Evaluates a single axis value against defined bounds.
    """
    b_min, b_max, is_provisional = get_regional_axis_bounds(region, axis)

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return RegionalBoundsDiagnostic(
            region=region,
            axis=axis,
            requested_value=float("nan"),
            bound_min=b_min,
            bound_max=b_max,
            is_valid=False,
            violation_amount=float("inf"),
            is_provisional=is_provisional,
            reason=f"Value must be numeric, got {type(value).__name__}.",
        )

    if math.isnan(value) or math.isinf(value):
        return RegionalBoundsDiagnostic(
            region=region,
            axis=axis,
            requested_value=value,
            bound_min=b_min,
            bound_max=b_max,
            is_valid=False,
            violation_amount=float("inf"),
            is_provisional=is_provisional,
            reason=f"Value cannot be non-finite ({value}).",
        )

    if value < b_min:
        violation = b_min - value
        reason = (
            f"Value {value:.4f} is below lower bound {b_min:.2f} for {region}.{axis} "
            f"({'provisional engineering limit' if is_provisional else 'general regional limit'})."
        )
        return RegionalBoundsDiagnostic(
            region=region,
            axis=axis,
            requested_value=value,
            bound_min=b_min,
            bound_max=b_max,
            is_valid=False,
            violation_amount=violation,
            is_provisional=is_provisional,
            reason=reason,
        )

    if value > b_max:
        violation = value - b_max
        reason = (
            f"Value {value:.4f} exceeds upper bound {b_max:.2f} for {region}.{axis} "
            f"({'provisional engineering limit' if is_provisional else 'general regional limit'})."
        )
        return RegionalBoundsDiagnostic(
            region=region,
            axis=axis,
            requested_value=value,
            bound_min=b_min,
            bound_max=b_max,
            is_valid=False,
            violation_amount=violation,
            is_provisional=is_provisional,
            reason=reason,
        )

    return RegionalBoundsDiagnostic(
        region=region,
        axis=axis,
        requested_value=value,
        bound_min=b_min,
        bound_max=b_max,
        is_valid=True,
        violation_amount=0.0,
        is_provisional=is_provisional,
        reason=None,
    )


def evaluate_regional_bounds(
    regional_scales: Dict[str, RegionalShapeScale]
) -> BoundsCheckReport:
    """
    Evaluates all axes of all regional shape scales.
    Returns a comprehensive BoundsCheckReport.
    """
    diagnostics: List[RegionalBoundsDiagnostic] = []
    violations_count = 0

    for region, scale in regional_scales.items():
        d_x = check_axis_bound(region, "scale_x", scale.scale_x)
        d_y = check_axis_bound(region, "scale_y", scale.scale_y)
        d_z = check_axis_bound(region, "scale_z", scale.scale_z)

        for diag in (d_x, d_y, d_z):
            diagnostics.append(diag)
            if not diag.is_valid:
                violations_count += 1

    is_valid = violations_count == 0
    if is_valid:
        summary = "All regional scale axes conform to defined bounds."
    else:
        summary = f"{violations_count} regional axis bound violations detected."

    return BoundsCheckReport(
        is_valid=is_valid,
        violations_count=violations_count,
        diagnostics=diagnostics,
        provisional_notice=BOUNDS_PROVISIONAL_NOTICE,
        summary_notes=summary,
    )


def validate_regional_bounds(
    regional_scales: Dict[str, RegionalShapeScale],
    raise_on_error: bool = True,
) -> BoundsCheckReport:
    """
    Validates regional bounds and optionally raises BICEBoundsExceededError on violation.
    """
    report = evaluate_regional_bounds(regional_scales)
    if not report.is_valid and raise_on_error:
        reasons = [d.reason for d in report.diagnostics if not d.is_valid and d.reason]
        raise BICEBoundsExceededError(
            f"Regional bounds validation failed: {'; '.join(reasons)}"
        )
    return report
