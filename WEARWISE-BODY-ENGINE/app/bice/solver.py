"""
WearWise BICE Solver and Shape Specification Builder
Constructs validated, engine-neutral AvatarShapeSpec candidate instances.
Evaluates candidate admissibility against provisional bounds and geometric locality feedback.
Keeps optimizer objective isolated and configurable.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Protocol, Union, Any
from uuid import uuid4

from app.domain.entities.avatar import AvatarShapeSpec, RegionalShapeScale
from app.domain.entities.body import BodyShapeControls, BodyMeasurement
from app.domain.interfaces.avatar import ShapeEvaluationPort
from app.bice.config import BICE_SPEC_VERSION, MAPPING_VERSION
from app.bice.normalizer import normalize_controls
from app.bice.mapping import map_normalized_to_regional_scales
from app.bice.bounds import (
    evaluate_regional_bounds,
    validate_regional_bounds,
    BoundsCheckReport,
)
from app.bice.validator import (
    validate_presentation,
    validate_stature,
    validate_controls_input,
    validate_measurements_input,
)
from app.bice.locality import (
    LocalityEvaluator,
    LocalityLossEvaluation,
)
from app.bice.exceptions import (
    BICEValidationError,
    BICEBoundsExceededError,
)


@dataclass(frozen=True)
class SolverCandidateDiagnostic:
    """Diagnostic tracking record for an evaluated candidate shape spec."""
    candidate_id: str
    shape_spec: AvatarShapeSpec
    bounds_report: BoundsCheckReport
    locality_evaluation: Optional[LocalityLossEvaluation]
    is_accepted: bool
    rejection_reason: Optional[str]
    metadata: Dict[str, Any]


class SolverObjectiveProtocol(Protocol):
    """Abstract interface for regularized solver objective functions."""
    def evaluate_loss(
        self,
        candidate_spec: AvatarShapeSpec,
        target_measurements: Dict[str, float],
        target_controls: Dict[str, float],
        locality_evaluation: Optional[LocalityLossEvaluation] = None,
    ) -> float:
        """Computes aggregate scalar regularized loss for the candidate."""
        ...


def build_avatar_shape_spec(
    presentation: str,
    stature_cm: Union[float, Decimal, int],
    measurements: Union[Dict[str, BodyMeasurement], Dict[str, Union[float, Decimal]]],
    controls: Union[BodyShapeControls, Dict[str, float]],
    regional_scales: Optional[Dict[str, RegionalShapeScale]] = None,
    spec_version: str = BICE_SPEC_VERSION,
    mapping_version: str = MAPPING_VERSION,
) -> AvatarShapeSpec:
    """
    Constructs a validated, immutable AvatarShapeSpec domain entity.
    Grounded in physical measurements and normalized regional scaling intent.
    Completely decoupled from avatar engines and PyTorch.
    """
    valid_presentation = validate_presentation(presentation)
    valid_stature = validate_stature(stature_cm)
    valid_measurements = validate_measurements_input(measurements)
    valid_controls = validate_controls_input(controls)

    # Ensure stature is present in target_measurements dictionary
    if "stature" not in valid_measurements:
        valid_measurements["stature"] = valid_stature

    # If regional_scales not explicitly provided, map from validated controls
    if regional_scales is None:
        norm_controls = normalize_controls(valid_controls)
        regional_scales = map_normalized_to_regional_scales(
            norm_controls, mapping_version=mapping_version
        )

    # Validate regional scale invariants and bounds
    validate_regional_bounds(regional_scales, raise_on_error=True)

    return AvatarShapeSpec(
        spec_version=spec_version,
        presentation=valid_presentation,  # type: ignore
        target_stature_cm=valid_stature,
        target_measurements=valid_measurements,
        regional_scales=regional_scales,
        semantic_controls=valid_controls,
    )


class BICEShapeSolver:
    """
    Body Intelligence & Calibration Engine Solver Framework.
    Manages candidate construction, bounds validation, and geometric locality evaluation.
    """
    def __init__(
        self,
        evaluation_port: Optional[ShapeEvaluationPort] = None,
        objective: Optional[SolverObjectiveProtocol] = None,
        spec_version: str = BICE_SPEC_VERSION,
        mapping_version: str = MAPPING_VERSION,
    ) -> None:
        self.evaluation_port = evaluation_port
        self.objective = objective
        self.spec_version = spec_version
        self.mapping_version = mapping_version
        self.locality_evaluator = (
            LocalityEvaluator(evaluation_port) if evaluation_port is not None else None
        )

    def generate_candidate(
        self,
        presentation: str,
        stature_cm: Union[float, Decimal, int],
        measurements: Union[Dict[str, BodyMeasurement], Dict[str, Union[float, Decimal]]],
        controls: Union[BodyShapeControls, Dict[str, float]],
        target_region: Optional[str] = None,
        candidate_regional_scales: Optional[Dict[str, RegionalShapeScale]] = None,
    ) -> SolverCandidateDiagnostic:
        """
        Generates a candidate AvatarShapeSpec and evaluates its admissibility.
        If candidate_regional_scales is provided (e.g. from an optimizer step), it is evaluated directly;
        otherwise, regional scales are deterministically mapped from controls.
        """
        candidate_id = str(uuid4())

        # 1. Validation
        valid_pres = validate_presentation(presentation)
        valid_stat = validate_stature(stature_cm)
        valid_meas = validate_measurements_input(measurements)
        valid_ctrl = validate_controls_input(controls)

        if "stature" not in valid_meas:
            valid_meas["stature"] = valid_stat

        # 2. Semantic normalization & regional mapping
        if candidate_regional_scales is not None:
            reg_scales = candidate_regional_scales
        else:
            norm_ctrl = normalize_controls(valid_ctrl)
            reg_scales = map_normalized_to_regional_scales(
                norm_ctrl, mapping_version=self.mapping_version
            )

        # 3. Regional bounds check
        bounds_report = evaluate_regional_bounds(reg_scales)

        # 4. Construct candidate spec
        shape_spec = AvatarShapeSpec(
            spec_version=self.spec_version,
            presentation=valid_pres,  # type: ignore
            target_stature_cm=valid_stat,
            target_measurements=valid_meas,
            regional_scales=reg_scales,
            semantic_controls=valid_ctrl,
        )

        # 5. Locality evaluation (if port is provided and target_region specified)
        locality_eval: Optional[LocalityLossEvaluation] = None
        if self.locality_evaluator is not None and target_region is not None:
            locality_eval = self.locality_evaluator.evaluate_locality(
                shape_spec=shape_spec,
                target_region=target_region,
            )

        # 6. Admissibility determination
        is_accepted = True
        rejection_reason = None

        if not bounds_report.is_valid:
            is_accepted = False
            rejection_reason = f"Bounds violation: {bounds_report.summary_notes}"
        elif locality_eval is not None and not locality_eval.is_valid:
            is_accepted = False
            rejection_reason = f"Locality violation: {locality_eval.diagnostic_notes}"

        return SolverCandidateDiagnostic(
            candidate_id=candidate_id,
            shape_spec=shape_spec,
            bounds_report=bounds_report,
            locality_evaluation=locality_eval,
            is_accepted=is_accepted,
            rejection_reason=rejection_reason,
            metadata={
                "mapping_version": self.mapping_version,
                "spec_version": self.spec_version,
            },
        )
