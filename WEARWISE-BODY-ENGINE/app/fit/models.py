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
class GarmentMeasurementProvenance:
    """
    Source metadata and audit provenance for physical garment finished dimensions.
    Distinguishes physical lab measurements from demonstration fixtures and brand specs,
    disclaiming certified physical measurement validation without verified empirical evidence.
    """
    sample_id: str                      # Unique physical garment or fixture ID, e.g. "WW-FIXTURE-TSHIRT-2026-001"
    data_origin: str                    # "demonstration_fixture", "physical_sample_measured", "brand_size_specification"
    measuring_instrument: str           # e.g. "calibrated_rigid_steel_tape_iso_standard", "flexible_fiberglass_tailoring_tape", "synthetic_fixture_generator"
    measurement_procedure: str          # e.g. "flat_relaxed_tabletop_bs_4952", "brand_tech_pack_specification"
    measurement_date: str               # ISO 8601 date, e.g. "2026-11-23"
    operator_id: str                    # e.g. "wearwise_qa_inspection_lab"
    validation_claim: str = "demonstration_fixture_provisional_not_certified"  # Disclaims certified physical calibration
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "data_origin": self.data_origin,
            "measuring_instrument": self.measuring_instrument,
            "measurement_procedure": self.measurement_procedure,
            "measurement_date": self.measurement_date,
            "operator_id": self.operator_id,
            "validation_claim": self.validation_claim,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class GarmentInputSpec:
    """Finished physical garment specifications measured directly or provided by brand."""
    title: str
    category: str
    size_label: str
    dimensions_cm: Dict[str, float]
    silhouette: str = "regular"
    fabric_properties: Optional[FabricProperties] = None
    provenance: Optional[GarmentMeasurementProvenance] = None
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
    garment_provenance: Optional[Dict[str, Any]] = None
    fabric_properties: Optional[Dict[str, Any]] = None
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
            "garment_provenance": self.garment_provenance,
            "fabric_properties": self.fabric_properties,
            "regional_evaluations": {
                k: v.to_dict() for k, v in self.regional_results.items()
            },
            "summary_explanation": self.summary_explanation,
            "disclaimer": self.disclaimer,
            "rulebook_version": self.rulebook_version,
            "evaluated_at": self.evaluated_at.isoformat(),
        }
