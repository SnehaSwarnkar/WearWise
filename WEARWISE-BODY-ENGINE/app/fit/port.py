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

        return sorted(reports, key=sort_key)

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
