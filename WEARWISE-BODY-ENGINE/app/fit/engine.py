"""
WearWise Honest Fit Engine
Core deterministic ease computation, 6-tier classification, discounted evidence coverage,
quadratic penalty scoring, and transparent natural language explanation generation.
"""

from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

from app.domain.entities.body import BodyMeasurement
from app.domain.taxonomies.measurement import (
    MeasurementAssessmentState,
    MeasurementValidationState,
)
from app.domain.taxonomies.garment import (
    RegionalFitClassification,
    FabricStretchDirection,
)
from app.fit.rulebook import (
    PROVISIONAL_EASE_INTERVALS,
    MINIMUM_WEARABLE_EASE,
    BASELINE_REGIONAL_WEIGHTS,
    DEFAULT_BETA_COEFFICIENTS,
    RULEBOOK_VERSION,
)
from app.fit.registry import (
    MeasurementCompatibilityRegistry,
    DimensionTransformation,
)
from app.fit.models import (
    GarmentInputSpec,
    RegionalFitResult,
    FitEvaluationReport,
)


class HonestFitEngine:
    """
    Deterministic Honest Fit Engine implementing HFE-001 Rev 1.2.1.
    Decoupled from iterative optimization, external frameworks, and persistence.
    """

    def __init__(
        self,
        beta_coefficients: Optional[Dict[str, float]] = None,
        rulebook_intervals: Optional[Dict[str, Dict[RegionalFitClassification, Tuple[float, float]]]] = None,
    ):
        self.beta_coefficients = beta_coefficients or DEFAULT_BETA_COEFFICIENTS.copy()
        self.intervals = rulebook_intervals or PROVISIONAL_EASE_INTERVALS

    # -------------------------------------------------------------------------
    # 1. Deterministic Ease Calculation & Classification
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_ease(garment_cm: float, body_cm: float) -> float:
        """Calculates dimensional ease in centimetres: Ease = Garment - Body."""
        return float(garment_cm) - float(body_cm)

    def classify_ease(self, dimension_code: str, ease_cm: float) -> RegionalFitClassification:
        """
        Classifies dimensional ease into exactly one of six non-overlapping intervals [low, high).
        Guarantees deterministic, non-ambiguous tier assignment.
        """
        table = self.intervals.get(dimension_code)
        if not table:
            raise KeyError(f"No ease rulebook configured for dimension: '{dimension_code}'")

        tier_order = [
            RegionalFitClassification.TOO_TIGHT,
            RegionalFitClassification.FITTED,
            RegionalFitClassification.REGULAR,
            RegionalFitClassification.RELAXED,
            RegionalFitClassification.OVERSIZED,
            RegionalFitClassification.TOO_LARGE,
        ]

        for tier in tier_order:
            low, high = table[tier]
            if low <= ease_cm < high:
                return tier

        # Default fallback for extreme numerical bounds
        if ease_cm < table[RegionalFitClassification.FITTED][0]:
            return RegionalFitClassification.TOO_TIGHT
        return RegionalFitClassification.TOO_LARGE

    def get_target_interval(
        self,
        dimension_code: str,
        preferred_silhouette: str,
    ) -> Tuple[float, float]:
        """Returns the [low, high) ease interval corresponding to the user's preferred silhouette."""
        table = self.intervals.get(dimension_code)
        if not table:
            raise KeyError(f"No ease rulebook for dimension: '{dimension_code}'")

        sil_norm = preferred_silhouette.lower().strip()
        pref_map = {
            "tight": RegionalFitClassification.TOO_TIGHT,
            "too_tight": RegionalFitClassification.TOO_TIGHT,
            "fitted": RegionalFitClassification.FITTED,
            "regular": RegionalFitClassification.REGULAR,
            "relaxed": RegionalFitClassification.RELAXED,
            "oversized": RegionalFitClassification.OVERSIZED,
            "too_large": RegionalFitClassification.TOO_LARGE,
        }
        target_tier = pref_map.get(sil_norm, RegionalFitClassification.REGULAR)
        return table[target_tier]

    @staticmethod
    def calculate_deviation(ease_cm: float, target_interval: Tuple[float, float]) -> float:
        """
        Calculates distance from target interval [low, high):
        d = max(0.0, low - ease, ease - high).
        """
        low, high = target_interval
        if ease_cm < low:
            return float(low - ease_cm)
        elif ease_cm >= high:
            return float(ease_cm - high)
        return 0.0

    def calculate_penalty(
        self,
        dimension_code: str,
        ease_cm: float,
        target_interval: Tuple[float, float],
        is_rigid: bool = True,
        beta_override: Optional[float] = None,
    ) -> float:
        """
        Computes the quadratic penalty for deviation from target ease interval.
        Penalty = min(100.0, beta * d^2).
        If ease is below minimum wearable in rigid fabric, Penalty = 100.0 (unwearable rejection).
        """
        min_wearable = MINIMUM_WEARABLE_EASE.get(dimension_code, 0.0)
        if is_rigid and ease_cm < min_wearable:
            return 100.0

        d = self.calculate_deviation(ease_cm, target_interval)
        if d <= 0.0:
            return 0.0

        beta = beta_override if beta_override is not None else self.beta_coefficients.get(dimension_code, 2.0)
        loss = beta * (d ** 2)
        return min(100.0, float(loss))

    # -------------------------------------------------------------------------
    # 2. Evidence Weighting & Coverage Calculation
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_effective_weight(
        body_meas: Optional[BodyMeasurement],
        baseline_weight: float,
    ) -> float:
        """
        Applies HFE-001 Section 4.1 effective measurement weighting:
        - ELIGIBLE: 1.0 * baseline_weight
        - PROVISIONAL: 0.5 * baseline_weight
        - DISPUTED / REJECTED / UNASSESSED / MISSING: 0.0
        """
        if body_meas is None:
            return 0.0

        # Disputed validity completely suppresses weight
        if body_meas.validation_state == MeasurementValidationState.DISPUTED:
            return 0.0

        if body_meas.assessment_state == MeasurementAssessmentState.ELIGIBLE:
            return 1.0 * float(baseline_weight)
        elif body_meas.assessment_state == MeasurementAssessmentState.PROVISIONAL:
            return 0.5 * float(baseline_weight)

        return 0.0

    @staticmethod
    def calculate_evidence_coverage(
        evaluated_effective_weights: Dict[str, float],
        required_body_dimensions: List[str],
        category_baseline_weights: Dict[str, float],
    ) -> float:
        """
        Calculates Evidence Coverage Ratio C(s) per HFE-001 Section 4.2:
        Numerator: sum of effective weights w_k' of evaluated dimensions.
        Denominator: sum of full baseline weights w_k of required dimensions.
        """
        denom = sum(
            category_baseline_weights.get(k, 0.20)
            for k in required_body_dimensions
        )
        if denom <= 0.0:
            denom = 1.0

        numer = sum(evaluated_effective_weights.values())
        return float(numer / denom)

    # -------------------------------------------------------------------------
    # 3. Transparent Human-Readable Explanations
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_regional_explanation(
        dimension_code: str,
        garment_cm: float,
        body_cm: float,
        ease_cm: float,
        classification: RegionalFitClassification,
    ) -> str:
        """Generates clear, transparent centimetre-based regional explanation."""
        sign = "+" if ease_cm >= 0 else ""
        ease_str = f"{sign}{ease_cm:.2f} cm"

        if dimension_code == "shoulder_biacromial_breadth":
            if ease_cm < -1.0:
                return (
                    f"Shoulder seams sit {abs(ease_cm):.1f} cm inside acromion bone "
                    f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), pulling tight across shoulders."
                )
            elif ease_cm <= 1.5:
                return (
                    f"Shoulder seams sit {ease_str} relative to acromion bone "
                    f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), providing tailored set-in shoulder alignment."
                )
            elif ease_cm <= 3.5:
                return (
                    f"Shoulder seams sit {ease_str} past acromion bone "
                    f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), offering standard relaxed shoulder drape."
                )
            else:
                return (
                    f"Shoulder seams sit {ease_str} past acromion bone "
                    f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), giving an intentional drop-shoulder silhouette."
                )

        if dimension_code == "chest_circumference":
            return (
                f"Chest girth has {ease_str} ease "
                f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), resulting in a {classification.value} fit."
            )

        if dimension_code == "waist_planar_circumference":
            return (
                f"Waist circumference has {ease_str} ease "
                f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), resulting in a {classification.value} fit."
            )

        if dimension_code == "hip_circumference":
            return (
                f"Hip / seat girth has {ease_str} ease "
                f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), resulting in a {classification.value} fit."
            )

        if dimension_code == "torso_length":
            if ease_cm < 0.0:
                return (
                    f"Garment hem sits {abs(ease_cm):.1f} cm above standard torso length "
                    f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), indicating cropped vertical coverage."
                )
            return (
                f"Garment hem extends {ease_str} past torso baseline "
                f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), providing comfortable vertical body coverage."
            )

        return (
            f"{dimension_code.replace('_', ' ').title()} has {ease_str} ease "
            f"(garment {garment_cm:.1f} cm vs body {body_cm:.1f} cm), rated {classification.value}."
        )

    # -------------------------------------------------------------------------
    # 4. Comprehensive Fit Evaluation Workflow
    # -------------------------------------------------------------------------

    def evaluate_fit(
        self,
        body_measurements: Dict[str, BodyMeasurement],
        garment: GarmentInputSpec,
        user_preference: str = "regular",
        beta_policy: Optional[Dict[str, float]] = None,
    ) -> FitEvaluationReport:
        """
        Executes end-to-end Honest Fit evaluation for a garment size:
        1. Resolves compatible dimensions from registry.
        2. Computes ease and non-overlapping classifications.
        3. Applies effective weighting (1.0 for ELIGIBLE, 0.5 for PROVISIONAL, 0 for missing/disputed).
        4. Enforces the 70% Evidence Coverage gate.
        5. Computes normalized bounded score [0.0, 100.0].
        6. Formulates transparent explanations and status.
        """
        cat = garment.category.lower().strip()
        cat_baseline_weights = BASELINE_REGIONAL_WEIGHTS.get(cat, BASELINE_REGIONAL_WEIGHTS["t_shirt"])
        required_body_codes = MeasurementCompatibilityRegistry.get_required_core_body_dimensions(cat)

        # Check fabric mechanical properties
        is_rigid = True
        if garment.fabric_properties:
            if garment.fabric_properties.stretch_direction != FabricStretchDirection.RIGID_ZERO:
                if garment.fabric_properties.mechanical_stretch_pct >= 0.05:
                    is_rigid = False

        # Transform garment input dimensions into equivalent canonical body dimension values
        garment_transformed_dims: Dict[str, float] = {}
        for g_code, raw_val in garment.dimensions_cm.items():
            if MeasurementCompatibilityRegistry.is_deferred(g_code):
                continue
            mapping = MeasurementCompatibilityRegistry.get_mapping(g_code)
            if mapping:
                b_code, transformed_val = MeasurementCompatibilityRegistry.transform_garment_dimension(
                    g_code, raw_val
                )
                garment_transformed_dims[b_code] = transformed_val

        # Identify missing required dimensions and unsupported dimensions
        missing_required = []
        for b_code in required_body_codes:
            if b_code not in body_measurements or body_measurements[b_code] is None:
                missing_required.append(b_code)
            elif b_code not in garment_transformed_dims:
                missing_required.append(b_code)

        unsupported = [
            b_code for b_code in MeasurementCompatibilityRegistry.CURRENTLY_UNAVAILABLE_BODY_CODES
            if b_code in required_body_codes
        ]

        # Evaluate compatible regions
        regional_results: Dict[str, RegionalFitResult] = {}
        effective_weights: Dict[str, float] = {}
        unwearable_detected = False

        for b_code, g_val in garment_transformed_dims.items():
            body_meas = body_measurements.get(b_code)
            if body_meas is None:
                continue

            base_w = cat_baseline_weights.get(b_code, 0.20)
            eff_w = self.calculate_effective_weight(body_meas, base_w)
            effective_weights[b_code] = eff_w

            b_val = float(body_meas.value_cm)
            ease = self.calculate_ease(g_val, b_val)
            classification = self.classify_ease(b_code, ease)
            target_interval = self.get_target_interval(b_code, user_preference)
            dev = self.calculate_deviation(ease, target_interval)

            beta = (
                beta_policy.get(b_code)
                if beta_policy and b_code in beta_policy
                else self.beta_coefficients.get(b_code, 2.0)
            )
            penalty = self.calculate_penalty(b_code, ease, target_interval, is_rigid=is_rigid, beta_override=beta)

            if penalty >= 100.0 and is_rigid and ease < MINIMUM_WEARABLE_EASE.get(b_code, 0.0):
                unwearable_detected = True

            explanation = self.generate_regional_explanation(
                b_code, g_val, b_val, ease, classification
            )

            regional_results[b_code] = RegionalFitResult(
                region_code=b_code,
                body_measurement_cm=b_val,
                garment_dimension_cm=g_val,
                ease_cm=ease,
                classification=classification,
                target_interval=target_interval,
                deviation_cm=dev,
                penalty=penalty,
                baseline_weight=base_w,
                effective_weight=eff_w,
                assessment_state=body_meas.assessment_state.value,
                explanation=explanation,
            )

        # Evidence coverage ratio C(s)
        coverage_ratio = self.calculate_evidence_coverage(
            effective_weights, required_body_codes, cat_baseline_weights
        )
        coverage_gate_passed = coverage_ratio >= 0.70

        # Handle Insufficient Evidence Gate (< 70%)
        if not coverage_gate_passed:
            status = "insufficient_data"
            composite_score = 0.0
            missing_names = ", ".join(m.replace("_", " ") for m in missing_required) or "required body dimensions"
            summary_explanation = (
                f"Insufficient body measurement evidence ({coverage_ratio * 100:.1f}% coverage, 70.0% required). "
                f"Please provide {missing_names} to evaluate honest fit."
            )
            return FitEvaluationReport(
                garment_title=garment.title,
                garment_category=garment.category,
                size_label=garment.size_label,
                silhouette_preference=user_preference,
                composite_score=composite_score,
                coverage_ratio=coverage_ratio,
                is_coverage_gate_passed=coverage_gate_passed,
                status=status,
                regional_results=regional_results,
                evaluated_dimensions=list(regional_results.keys()),
                missing_required_dimensions=missing_required,
                unsupported_dimensions=unsupported,
                summary_explanation=summary_explanation,
            )

        # Compute normalized composite fit score
        sum_eff_w = sum(effective_weights.values())
        if sum_eff_w <= 0.0:
            composite_score = 0.0
        else:
            weighted_penalties = 0.0
            for b_code, res in regional_results.items():
                w_norm = effective_weights[b_code] / sum_eff_w
                weighted_penalties += w_norm * res.penalty
            composite_score = max(0.0, min(100.0, 100.0 - weighted_penalties))

        # Determine recommendation status
        if unwearable_detected:
            status = "rejected_unwearable"
            summary_explanation = (
                f"Size {garment.size_label} is rejected as unwearable: one or more regions have insufficient ease "
                f"for non-stretch fabric, causing severe constriction."
            )
        elif composite_score >= 85.0:
            status = "recommended"
            summary_explanation = (
                f"Size {garment.size_label} is recommended for your preferred {user_preference.title()} fit "
                f"(Provisional Fit Score: {composite_score:.1f} / 100)."
            )
        elif composite_score >= 60.0:
            status = "alternative"
            summary_explanation = (
                f"Size {garment.size_label} is a wearable alternative "
                f"(Provisional Fit Score: {composite_score:.1f} / 100) with minor regional silhouette deviations."
            )
        else:
            status = "poor_fit"
            summary_explanation = (
                f"Size {garment.size_label} has significant silhouette mismatch "
                f"(Provisional Fit Score: {composite_score:.1f} / 100) relative to your {user_preference} preference."
            )

        return FitEvaluationReport(
            garment_title=garment.title,
            garment_category=garment.category,
            size_label=garment.size_label,
            silhouette_preference=user_preference,
            composite_score=composite_score,
            coverage_ratio=coverage_ratio,
            is_coverage_gate_passed=coverage_gate_passed,
            status=status,
            regional_results=regional_results,
            evaluated_dimensions=list(regional_results.keys()),
            missing_required_dimensions=missing_required,
            unsupported_dimensions=unsupported,
            summary_explanation=summary_explanation,
        )
