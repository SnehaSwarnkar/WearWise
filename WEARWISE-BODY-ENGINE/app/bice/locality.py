"""
WearWise BICE Geometric Locality Evaluator
Calculates Regional Mean Spillover Ratio (RMSR) and locality loss L_locality
using the engine-neutral ShapeEvaluationPort and ShapeEvaluationResult contracts.

Enforces strict near-zero target signal policy (threshold 1e-4 m) and maximal penalty (10.0).
Zero coupling to PyTorch or concrete avatar engines.
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Optional
from app.domain.entities.avatar import AvatarShapeSpec, ShapeEvaluationResult
from app.domain.interfaces.avatar import ShapeEvaluationPort
from app.bice.config import TARGET_SIGNAL_THRESHOLD_M, MAXIMAL_LOCALITY_PENALTY
from app.bice.exceptions import BICEInsufficientSignalError, BICEValidationError


@dataclass(frozen=True)
class LocalityLossEvaluation:
    """Structured evaluation result for cross-regional geometric spillover."""
    locality_loss: float
    rmsr_by_region: Dict[str, float]
    target_region: str
    target_displacement_m: float
    max_non_target_displacement_m: float
    max_spillover_region: Optional[str]
    status: str
    is_valid: bool
    diagnostic_notes: str


def compute_rmsr(
    mean_region_m: float,
    mean_target_m: float,
    threshold_m: float = TARGET_SIGNAL_THRESHOLD_M,
) -> Optional[float]:
    """
    Computes RMSR_R = mean_displacement_R / mean_displacement_R_target.
    Returns None if target displacement is below numerical threshold.
    """
    if (
        not isinstance(mean_region_m, (int, float))
        or not isinstance(mean_target_m, (int, float))
        or isinstance(mean_region_m, bool)
        or isinstance(mean_target_m, bool)
    ):
        raise BICEValidationError("Displacement magnitudes must be numeric.")

    if math.isnan(mean_region_m) or math.isnan(mean_target_m):
        return None

    if math.isinf(mean_region_m) or math.isinf(mean_target_m):
        return None

    if mean_region_m < 0.0 or mean_target_m < 0.0:
        return None

    if mean_target_m < threshold_m:
        return None

    return mean_region_m / mean_target_m


def evaluate_locality_from_result(
    result: ShapeEvaluationResult,
    target_region: str,
    threshold_m: float = TARGET_SIGNAL_THRESHOLD_M,
    penalty_max: float = MAXIMAL_LOCALITY_PENALTY,
) -> LocalityLossEvaluation:
    """
    Evaluates locality loss and regional spillover from a ShapeEvaluationResult.
    Enforces near-zero signal rejection and maximal penalty policy.
    """
    # 1. Plausibility check
    if not result.is_plausible:
        return LocalityLossEvaluation(
            locality_loss=penalty_max,
            rmsr_by_region={},
            target_region=target_region,
            target_displacement_m=result.target_region_mean_m,
            max_non_target_displacement_m=result.max_non_target_mean_m,
            max_spillover_region=None,
            status="implausible_geometry",
            is_valid=False,
            diagnostic_notes=f"Candidate rejected: geometry marked implausible. {result.diagnostic_notes}",
        )

    # 2. Near-zero target signal policy (< 1e-4 m)
    if (
        result.evaluation_status == "insufficient_target_signal"
        or result.target_region_mean_m < threshold_m
        or result.rmsr is None
    ):
        return LocalityLossEvaluation(
            locality_loss=penalty_max,
            rmsr_by_region={},
            target_region=target_region,
            target_displacement_m=result.target_region_mean_m,
            max_non_target_displacement_m=result.max_non_target_mean_m,
            max_spillover_region=None,
            status="insufficient_target_signal",
            is_valid=False,
            diagnostic_notes=(
                f"Candidate step rejected: target region '{target_region}' mean displacement "
                f"({result.target_region_mean_m:.6e} m) is below evaluation threshold ({threshold_m:.1e} m). "
                f"Assigned maximal locality penalty {penalty_max:.1f}. Uninformative gradient direction."
            ),
        )

    # 3. Compute RMSR per non-target region
    rmsr_by_region: Dict[str, float] = {}
    max_rmsr = 0.0
    max_region: Optional[str] = None

    for region, summary in result.regional_displacements.items():
        if region == target_region:
            continue
        ratio = compute_rmsr(
            summary.mean_displacement_m,
            result.target_region_mean_m,
            threshold_m=threshold_m,
        )
        if ratio is not None:
            rmsr_by_region[region] = ratio
            if ratio > max_rmsr:
                max_rmsr = ratio
                max_region = region

    # Locality loss is max RMSR across non-target regions
    locality_loss = max_rmsr

    return LocalityLossEvaluation(
        locality_loss=locality_loss,
        rmsr_by_region=rmsr_by_region,
        target_region=target_region,
        target_displacement_m=result.target_region_mean_m,
        max_non_target_displacement_m=result.max_non_target_mean_m,
        max_spillover_region=max_region,
        status="success",
        is_valid=True,
        diagnostic_notes=(
            f"Locality evaluated successfully. Max spillover RMSR={locality_loss:.4f} "
            f"in region '{max_region}'."
        ),
    )


class LocalityEvaluator:
    """
    Engine-neutral evaluator consuming injected ShapeEvaluationPort.
    """
    def __init__(
        self,
        evaluation_port: ShapeEvaluationPort,
        threshold_m: float = TARGET_SIGNAL_THRESHOLD_M,
        penalty_max: float = MAXIMAL_LOCALITY_PENALTY,
    ) -> None:
        self.evaluation_port = evaluation_port
        self.threshold_m = threshold_m
        self.penalty_max = penalty_max

    def evaluate_locality(
        self,
        shape_spec: AvatarShapeSpec,
        target_region: str,
        requested_regions: Optional[List[str]] = None,
    ) -> LocalityLossEvaluation:
        """
        Executes evaluation against injected port and calculates locality loss.
        """
        if requested_regions is None:
            requested_regions = list(shape_spec.regional_scales.keys())

        res = self.evaluation_port.evaluate_shape(
            shape_spec=shape_spec,
            target_region=target_region,
            requested_regions=requested_regions,
        )

        return evaluate_locality_from_result(
            result=res,
            target_region=target_region,
            threshold_m=self.threshold_m,
            penalty_max=self.penalty_max,
        )
