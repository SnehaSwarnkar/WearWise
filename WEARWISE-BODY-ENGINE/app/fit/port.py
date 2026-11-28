"""
WearWise Honest Fit Evaluation Port
Clean boundary adapter connecting body anthropometric measurements and physical garment specifications.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from uuid import UUID

from app.domain.entities.body import BodyMeasurement
from app.fit.models import GarmentInputSpec, FitEvaluationReport
from app.fit.engine import HonestFitEngine


class HonestFitEvaluationPort:
    """
    Application port interface for executing honest fit evaluations.
    Decoupled from persistence, HTTP controllers, and avatar 3D engines.
    """

    def __init__(self, engine: Optional[HonestFitEngine] = None):
        self.engine = engine or HonestFitEngine()

    def evaluate_garment_size(
        self,
        body_measurements: Dict[str, BodyMeasurement],
        garment: GarmentInputSpec,
        user_preference: str = "regular",
        beta_policy: Optional[Dict[str, float]] = None,
    ) -> FitEvaluationReport:
        """Evaluates a single garment size against the user's active body measurements."""
        return self.engine.evaluate_fit(
            body_measurements=body_measurements,
            garment=garment,
            user_preference=user_preference,
            beta_policy=beta_policy,
        )

    def evaluate_multi_size_garment(
        self,
        body_measurements: Dict[str, BodyMeasurement],
        garment_sizes: List[GarmentInputSpec],
        user_preference: str = "regular",
        beta_policy: Optional[Dict[str, float]] = None,
    ) -> List[FitEvaluationReport]:
        """
        Evaluates a collection of sizes for a garment (e.g. S, M, L, XL),
        returning reports sorted by composite fit score descending.
        """
        reports = [
            self.evaluate_garment_size(
                body_measurements=body_measurements,
                garment=size_spec,
                user_preference=user_preference,
                beta_policy=beta_policy,
            )
            for size_spec in garment_sizes
        ]
        # Sort by score descending (with insufficient_data / unwearable at end)
        def sort_key(r: FitEvaluationReport) -> Tuple[int, float]:
            if r.status == "recommended":
                priority = 0
            elif r.status == "alternative":
                priority = 1
            elif r.status == "poor_fit":
                priority = 2
            elif r.status == "rejected_unwearable":
                priority = 3
            else:
                priority = 4
            return (priority, -r.composite_score)

        sorted_reports = sorted(reports, key=sort_key)

        # Enforce single top recommendation invariant:
        # In a multi-size evaluation, exactly one size is designated 'recommended' (the top-ranked
        # wearable size), while other wearable sizes are consistently designated 'alternative'.
        final_reports: List[FitEvaluationReport] = []
        found_top_recommended = False

        for r in sorted_reports:
            if not found_top_recommended and r.status in ("recommended", "alternative") and r.is_coverage_gate_passed:
                found_top_recommended = True
                if r.status != "recommended":
                    r = FitEvaluationReport(
                        garment_title=r.garment_title,
                        garment_category=r.garment_category,
                        size_label=r.size_label,
                        silhouette_preference=r.silhouette_preference,
                        composite_score=r.composite_score,
                        coverage_ratio=r.coverage_ratio,
                        is_coverage_gate_passed=r.is_coverage_gate_passed,
                        status="recommended",
                        regional_results=r.regional_results,
                        evaluated_dimensions=r.evaluated_dimensions,
                        missing_required_dimensions=r.missing_required_dimensions,
                        unsupported_dimensions=r.unsupported_dimensions,
                        summary_explanation=f"Size {r.size_label} is recommended for your preferred {r.silhouette_preference.title()} fit (Provisional Fit Score: {r.composite_score:.1f} / 100).",
                        garment_provenance=r.garment_provenance,
                        fabric_properties=r.fabric_properties,
                        disclaimer=r.disclaimer,
                        rulebook_version=r.rulebook_version,
                        report_id=r.report_id,
                        evaluated_at=r.evaluated_at,
                    )
            elif found_top_recommended and r.status == "recommended":
                r = FitEvaluationReport(
                    garment_title=r.garment_title,
                    garment_category=r.garment_category,
                    size_label=r.size_label,
                    silhouette_preference=r.silhouette_preference,
                    composite_score=r.composite_score,
                    coverage_ratio=r.coverage_ratio,
                    is_coverage_gate_passed=r.is_coverage_gate_passed,
                    status="alternative",
                    regional_results=r.regional_results,
                    evaluated_dimensions=r.evaluated_dimensions,
                    missing_required_dimensions=r.missing_required_dimensions,
                    unsupported_dimensions=r.unsupported_dimensions,
                    summary_explanation=f"Size {r.size_label} is a wearable alternative (Provisional Fit Score: {r.composite_score:.1f} / 100) relative to your {r.silhouette_preference} preference.",
                    garment_provenance=r.garment_provenance,
                    fabric_properties=r.fabric_properties,
                    disclaimer=r.disclaimer,
                    rulebook_version=r.rulebook_version,
                    report_id=r.report_id,
                    evaluated_at=r.evaluated_at,
                )
            final_reports.append(r)

        return final_reports

    def recommend_best_size(
        self,
        body_measurements: Dict[str, BodyMeasurement],
        garment_sizes: List[GarmentInputSpec],
        user_preference: str = "regular",
        beta_policy: Optional[Dict[str, float]] = None,
    ) -> Optional[FitEvaluationReport]:
        """Returns the single top-scoring wearable size for the user's preferred silhouette."""
        evaluated = self.evaluate_multi_size_garment(
            body_measurements=body_measurements,
            garment_sizes=garment_sizes,
            user_preference=user_preference,
            beta_policy=beta_policy,
        )
        for r in evaluated:
            if r.is_coverage_gate_passed and r.status in ("recommended", "alternative"):
                return r
        return evaluated[0] if evaluated else None
