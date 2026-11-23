"""
Test Suite: BICE Geometric Locality Evaluation
Verifies RMSR calculation, maximum spillover loss, near-zero target signal policy,
maximal penalty assignment (10.0), and rejection of implausible geometry using test doubles.
"""

from typing import Dict, List, Optional
import pytest
from app.bice.locality import (
    compute_rmsr,
    evaluate_locality_from_result,
    LocalityEvaluator,
    LocalityLossEvaluation,
)
from app.bice.config import TARGET_SIGNAL_THRESHOLD_M, MAXIMAL_LOCALITY_PENALTY
from app.domain.entities.avatar import (
    AvatarShapeSpec,
    RegionalDisplacementSummary,
    ShapeEvaluationResult,
    RegionalShapeScale,
)
from app.domain.taxonomies.garment import PresentationGender
from app.domain.interfaces.avatar import ShapeEvaluationPort


class MockDeterministicEvaluationPort:
    """
    Deterministic test double implementing ShapeEvaluationPort protocol.
    Configured with predetermined regional displacements for reproducible unit tests.
    """
    def __init__(
        self,
        target_displacement_m: float,
        non_target_displacements_m: Dict[str, float],
        is_plausible: bool = True,
        status: str = "success",
    ) -> None:
        self.target_displacement_m = target_displacement_m
        self.non_target_displacements_m = non_target_displacements_m
        self.is_plausible = is_plausible
        self.status = status

    def evaluate_shape(
        self,
        shape_spec: AvatarShapeSpec,
        target_region: str,
        requested_regions: List[str],
    ) -> ShapeEvaluationResult:
        regional_displacements: Dict[str, RegionalDisplacementSummary] = {}

        regional_displacements[target_region] = RegionalDisplacementSummary(
            region_code=target_region,
            mean_displacement_m=self.target_displacement_m,
            max_displacement_m=self.target_displacement_m * 1.5,
            vertex_count=500,
        )

        max_non_target_m = 0.0
        for reg in requested_regions:
            if reg == target_region:
                continue
            disp = self.non_target_displacements_m.get(reg, 0.0)
            regional_displacements[reg] = RegionalDisplacementSummary(
                region_code=reg,
                mean_displacement_m=disp,
                max_displacement_m=disp * 1.5,
                vertex_count=300,
            )
            if disp > max_non_target_m:
                max_non_target_m = disp

        rmsr = (
            max_non_target_m / self.target_displacement_m
            if self.target_displacement_m >= TARGET_SIGNAL_THRESHOLD_M
            else None
        )

        return ShapeEvaluationResult(
            metric_version="1.2.1-rmsr-pvsr",
            evaluation_status=self.status,
            regional_displacements=regional_displacements,
            target_region_mean_m=self.target_displacement_m,
            max_non_target_mean_m=max_non_target_m,
            rmsr=rmsr,
            pvsr=rmsr,
            is_plausible=self.is_plausible,
            diagnostic_notes="Mock deterministic evaluation",
        )


def test_rmsr_arithmetic_calculation():
    """Verify compute_rmsr computes arithmetic ratio of mean displacements."""
    # Target 0.010 m (10 mm), Non-target 0.002 m (2 mm) -> RMSR = 0.20
    ratio = compute_rmsr(mean_region_m=0.002, mean_target_m=0.010)
    assert ratio == pytest.approx(0.20, abs=1e-5)


def test_near_zero_signal_returns_none_in_compute_rmsr():
    """Verify compute_rmsr returns None when target displacement is below 1e-4 m."""
    # Target 5e-5 m (< 1e-4 m threshold)
    ratio = compute_rmsr(mean_region_m=0.001, mean_target_m=5e-5)
    assert ratio is None


def test_near_zero_signal_policy_and_maximal_penalty():
    """
    Verify near-zero signal returns status 'insufficient_target_signal',
    applies maximal penalty 10.0, and never interprets missing RMSR as 0.0.
    """
    port = MockDeterministicEvaluationPort(
        target_displacement_m=5e-5,  # 0.05 mm, below 0.1 mm threshold
        non_target_displacements_m={"waist_abdomen": 1e-5},
        status="insufficient_target_signal",
    )
    evaluator = LocalityEvaluator(port)

    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.NEUTRAL,
        target_stature_cm=175.0,
        target_measurements={"stature": 175.0},
        regional_scales={"shoulders": RegionalShapeScale(0.1, 0.0, 0.0)},
        semantic_controls={"shoulder_width": 0.55},
    )

    eval_result = evaluator.evaluate_locality(spec, target_region="shoulders")

    assert eval_result.is_valid is False
    assert eval_result.status == "insufficient_target_signal"
    assert eval_result.locality_loss == MAXIMAL_LOCALITY_PENALTY
    assert eval_result.locality_loss != 0.0
    assert "Insufficient target signal" in eval_result.diagnostic_notes


def test_successful_locality_evaluation_and_max_spillover():
    """Verify successful evaluation identifies the region of maximal spillover."""
    port = MockDeterministicEvaluationPort(
        target_displacement_m=0.010,  # 10 mm
        non_target_displacements_m={
            "torso_chest": 0.002,     # RMSR = 0.20
            "waist_abdomen": 0.004,   # RMSR = 0.40 (Max)
            "hips": 0.001,            # RMSR = 0.10
        },
        status="success",
    )
    evaluator = LocalityEvaluator(port)

    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=180.0,
        target_measurements={"stature": 180.0},
        regional_scales={
            "shoulders": RegionalShapeScale(0.3, 0.0, 0.0),
            "torso_chest": RegionalShapeScale(0.0, 0.0, 0.0),
            "waist_abdomen": RegionalShapeScale(0.0, 0.0, 0.0),
            "hips": RegionalShapeScale(0.0, 0.0, 0.0),
        },
        semantic_controls={"shoulder_width": 0.65},
    )

    eval_result = evaluator.evaluate_locality(spec, target_region="shoulders")

    assert eval_result.is_valid is True
    assert eval_result.status == "success"
    assert eval_result.locality_loss == pytest.approx(0.40, abs=1e-5)
    assert eval_result.max_spillover_region == "waist_abdomen"
    assert eval_result.rmsr_by_region["torso_chest"] == pytest.approx(0.20, abs=1e-5)
    assert eval_result.rmsr_by_region["hips"] == pytest.approx(0.10, abs=1e-5)


def test_implausible_geometry_rejection():
    """Verify that geometry marked implausible is assigned maximal penalty 10.0."""
    port = MockDeterministicEvaluationPort(
        target_displacement_m=0.010,
        non_target_displacements_m={"waist_abdomen": 0.002},
        is_plausible=False,
    )
    evaluator = LocalityEvaluator(port)

    spec = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.NEUTRAL,
        target_stature_cm=170.0,
        target_measurements={"stature": 170.0},
        regional_scales={"shoulders": RegionalShapeScale(0.0, 0.0, 0.0)},
        semantic_controls={"shoulder_width": 0.50},
    )

    eval_result = evaluator.evaluate_locality(spec, target_region="shoulders")
    assert eval_result.is_valid is False
    assert eval_result.status == "implausible_geometry"
    assert eval_result.locality_loss == MAXIMAL_LOCALITY_PENALTY
