"""
WearWise Honest Fit Data Models
Pure Python dataclasses for garment input specifications, regional fit results, and evaluation reports.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from app.domain.taxonomies.garment import RegionalFitClassification
from app.domain.entities.garment import FabricProperties
from app.fit.rulebook import RULEBOOK_VERSION


@dataclass(frozen=True)
class GarmentInputSpec:
    """Finished physical garment specifications measured directly or provided by brand."""
    title: str
    category: str
    size_label: str
    dimensions_cm: Dict[str, float]
    silhouette: str = "regular"
    fabric_properties: Optional[FabricProperties] = None
    provenance: str = "physical_manual_measurement"
    garment_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class RegionalFitResult:
    """Detailed evaluation result for an individual anatomical body region."""
    region_code: str
    body_measurement_cm: float
    garment_dimension_cm: float
    ease_cm: float
    classification: RegionalFitClassification
    target_interval: Tuple[float, float]
    deviation_cm: float
    penalty: float
    baseline_weight: float
    effective_weight: float
    assessment_state: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_code": self.region_code,
            "body_measurement_cm": round(self.body_measurement_cm, 2),
            "garment_dimension_cm": round(self.garment_dimension_cm, 2),
            "ease_cm": round(self.ease_cm, 2),
            "classification": self.classification.value,
            "target_interval": [
                None if self.target_interval[0] == float("-inf") else round(self.target_interval[0], 2),
                None if self.target_interval[1] == float("inf") else round(self.target_interval[1], 2),
            ],
            "deviation_cm": round(self.deviation_cm, 2),
            "penalty": round(self.penalty, 2),
            "baseline_weight": round(self.baseline_weight, 3),
            "effective_weight": round(self.effective_weight, 3),
            "assessment_state": self.assessment_state,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class FitEvaluationReport:
    """Complete honest fit recommendation report for a garment size."""
    garment_title: str
    garment_category: str
    size_label: str
    silhouette_preference: str
    composite_score: float             # [0.0, 100.0]
    coverage_ratio: float              # [0.0, 1.0+]
    is_coverage_gate_passed: bool      # coverage_ratio >= 0.70
    status: str                        # "recommended", "alternative", "rejected_unwearable", "insufficient_data"
    regional_results: Dict[str, RegionalFitResult]
    evaluated_dimensions: List[str]
    missing_required_dimensions: List[str]
    unsupported_dimensions: List[str]
    summary_explanation: str
    disclaimer: str = (
        "Provisional engineering fit estimation per Rev 1.2.1. "
        "Thresholds subject to Phase 5 physical wear trial calibration."
    )
    rulebook_version: str = RULEBOOK_VERSION
    report_id: UUID = field(default_factory=uuid4)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": str(self.report_id),
            "garment_title": self.garment_title,
            "garment_category": self.garment_category,
            "size_label": self.size_label,
            "silhouette_preference": self.silhouette_preference,
            "composite_score": round(self.composite_score, 1),
            "coverage_ratio": round(self.coverage_ratio, 3),
            "coverage_percentage": f"{round(self.coverage_ratio * 100, 1)}%",
            "is_coverage_gate_passed": self.is_coverage_gate_passed,
            "status": self.status,
            "evaluated_dimensions": self.evaluated_dimensions,
            "missing_required_dimensions": self.missing_required_dimensions,
            "unsupported_dimensions": self.unsupported_dimensions,
            "regional_evaluations": {
                k: v.to_dict() for k, v in self.regional_results.items()
            },
            "summary_explanation": self.summary_explanation,
            "disclaimer": self.disclaimer,
            "rulebook_version": self.rulebook_version,
            "evaluated_at": self.evaluated_at.isoformat(),
        }
