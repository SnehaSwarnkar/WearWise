"""
WearWise Fit Recommendation Application Service
Executes Honest Fit evaluations connecting active body measurements and garment size dimensions.
Enforces profile ownership and persists recommendation results.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.domain.entities.body import BodyMeasurement
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import FabricStretchDirection
from app.domain.entities.garment import FabricProperties
from app.fit.models import GarmentInputSpec, GarmentMeasurementProvenance
from app.fit.port import HonestFitEvaluationPort
from app.fit.rulebook import RULEBOOK_VERSION
from app.repositories.profile_repository import ProfileRepository
from app.repositories.garment_repository import GarmentRepository
from app.repositories.fit_repository import FitRepository
from app.db.models import FitRecommendationModel
from app.services.errors import NotFoundError, ForbiddenError, ValidationError


class FitEvaluationService:
    """Application service for Honest Fit evaluation and recommendation persistence."""

    def __init__(self, db: Session, fit_port: Optional[HonestFitEvaluationPort] = None):
        self.db = db
        self.profile_repo = ProfileRepository(db)
        self.garment_repo = GarmentRepository(db)
        self.fit_repo = FitRepository(db)
        self.fit_port = fit_port or HonestFitEvaluationPort()

    def evaluate_fit(
        self,
        profile_id: uuid.UUID,
        garment_id: uuid.UUID,
        user_preference: str,
        requesting_user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Executes Honest Fit evaluation for user profile against merchant garment.
        1. Verifies profile ownership.
        2. Retrieves active body measurements from latest profile revision.
        3. Retrieves garment specification and size variants from latest garment revision.
        4. Invokes HonestFitEvaluationPort.
        5. Persists top recommendation to database.
        6. Returns structured fit report conforming to API_CONTRACTS.md.
        """
        profile = self.profile_repo.get_profile(profile_id)
        if not profile:
            raise NotFoundError(f"Profile {profile_id} not found.")

        if profile.user_id != requesting_user_id:
            raise ForbiddenError(
                "Access denied: You do not have permission to evaluate fit for this profile.",
                code="OWNERSHIP_VIOLATION",
            )

        latest_profile_rev = self.profile_repo.get_latest_revision(profile_id)
        if not latest_profile_rev:
            raise NotFoundError(f"Profile {profile_id} has no active revisions.")

        garment = self.garment_repo.get_garment(garment_id)
        if not garment:
            raise NotFoundError(f"Garment {garment_id} not found.")

        latest_garment_rev = self.garment_repo.get_latest_revision(garment_id)
        if not latest_garment_rev:
            raise NotFoundError(f"Garment {garment_id} has no active revisions.")

        if not latest_garment_rev.sizes:
            raise ValidationError(f"Garment {garment_id} has no size specifications defined.")

        # 1. Convert active DB body measurements to domain entities
        body_meas_dict: Dict[str, BodyMeasurement] = {}
        for m in latest_profile_rev.measurements:
            if m.lifecycle_status == "active":
                acq_method = MeasurementAcquisitionMethod(m.acquisition_method)
                val_state = MeasurementValidationState(m.validation_state)
                life_status = MeasurementLifecycleStatus(m.lifecycle_status)
                assess_state = MeasurementAssessmentState(m.assessment_state)

                body_meas_dict[m.measurement_code] = BodyMeasurement(
                    measurement_code=m.measurement_code,
                    value_cm=Decimal(str(m.value_cm)),
                    unit=m.unit,
                    acquisition_method=acq_method,
                    validation_state=val_state,
                    lifecycle_status=life_status,
                    assessment_state=assess_state,
                    landmark_convention=m.landmark_convention,
                    tolerance_cm=Decimal(str(m.tolerance_cm)),
                    reliability_weight=Decimal(str(m.reliability_weight)),
                )

        # 2. Extract fabric properties and provenance
        fp_json = latest_garment_rev.fabric_properties_json or {}
        fabric_props = FabricProperties(
            fibre_composition=fp_json.get("fibre_composition", {"cotton": 1.0}),
            mechanical_stretch_pct=float(fp_json.get("mechanical_stretch_pct", 0.015)),
            stretch_recovery_pct=float(fp_json.get("stretch_recovery_pct", 0.90)),
            stretch_direction=FabricStretchDirection(fp_json.get("stretch_direction", "rigid_zero")),
        )

        # 3. Build GarmentInputSpec for each size
        garment_size_specs: List[GarmentInputSpec] = []
        for s in latest_garment_rev.sizes:
            dim_dict = {m.dimension_code: float(m.value_cm) for m in s.measurements}
            # Pick first measurement provenance or standard default
            prov_model = s.measurements[0] if s.measurements else None
            provenance = None
            if prov_model:
                provenance = GarmentMeasurementProvenance(
                    sample_id=str(s.id),
                    data_origin=prov_model.provenance,
                    measuring_instrument="standard_apparel_tape",
                    measurement_procedure=prov_model.measurement_procedure,
                    measurement_date="2026-11-23",
                    operator_id="merchant_operator",
                    validation_claim="brand_certified_spec",
                )

            garment_size_specs.append(
                GarmentInputSpec(
                    title=garment.title,
                    category=garment.category,
                    size_label=s.size_label,
                    dimensions_cm=dim_dict,
                    fabric_properties=fabric_props,
                    provenance=provenance,
                    garment_id=str(garment.id),
                )
            )

        # 4. Evaluate multi-size garment fit
        reports = self.fit_port.evaluate_multi_size_garment(
            body_measurements=body_meas_dict,
            garment_sizes=garment_size_specs,
            user_preference=user_preference,
        )

        top_report = reports[0] if reports else None
        if not top_report:
            raise ValidationError("Unable to compute fit evaluation for the supplied garment and profile.")

        # 5. Extract alternative size if available
        alt_size_info = None
        for r in reports[1:]:
            if r.status == "alternative" and r.is_coverage_gate_passed:
                alt_size_info = {
                    "size_label": r.size_label,
                    "fit_summary": f"Alternative size ({r.composite_score:.1f}/100) — {r.summary_explanation}",
                }
                break

        # 6. Build regional comparison list
        regional_comparisons = []
        for reg, res in top_report.regional_results.items():
            regional_comparisons.append({
                "region": reg,
                "body_measurement_cm": res.body_measurement_cm,
                "garment_dimension_cm": res.garment_dimension_cm,
                "ease_cm": res.ease_cm,
                "classification": res.classification,
                "explanation": res.explanation,
            })

        # 7. Persist recommendation
        explanations_payload = {
            "silhouette_preference": top_report.silhouette_preference,
            "status": top_report.status,
            "coverage_ratio": top_report.coverage_ratio,
            "is_coverage_gate_passed": top_report.is_coverage_gate_passed,
            "summary_explanation": top_report.summary_explanation,
            "alternative_size": alt_size_info,
            "regional_comparisons": regional_comparisons,
            "all_size_evaluations": [
                {
                    "size_label": r.size_label,
                    "composite_score": r.composite_score,
                    "status": r.status,
                    "is_coverage_gate_passed": r.is_coverage_gate_passed,
                }
                for r in reports
            ],
            "disclaimer": "Illustrative sample score; ease thresholds and penalty coefficients are provisional baselines pending physical wear trials.",
        }

        rec_model = self.fit_repo.save_fit_recommendation(
            profile_revision_id=latest_profile_rev.id,
            garment_revision_id=latest_garment_rev.id,
            recommended_size=top_report.size_label,
            composite_score=Decimal(f"{top_report.composite_score:.1f}"),
            explanations_json=explanations_payload,
            rulebook_version=RULEBOOK_VERSION,
        )

        return {
            "recommendation_id": str(rec_model.id),
            "garment_id": str(garment.id),
            "recommended_size": top_report.size_label,
            "composite_fit_score": round(float(top_report.composite_score), 1),
            "status": top_report.status,
            "alternative_size": alt_size_info,
            "regional_comparisons": regional_comparisons,
            "disclaimer": explanations_payload["disclaimer"],
        }

    def get_recommendation(
        self,
        recommendation_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Retrieves persisted recommendation after checking profile ownership."""
        rec = self.fit_repo.get_fit_recommendation(recommendation_id)
        if not rec:
            raise NotFoundError(f"Fit recommendation {recommendation_id} not found.")

        owner_user_id = rec.profile_revision.profile.user_id
        if owner_user_id != requesting_user_id:
            raise ForbiddenError("Access denied: You do not own this fit recommendation.", code="OWNERSHIP_VIOLATION")

        exp = rec.explanations_json or {}
        return {
            "recommendation_id": str(rec.id),
            "garment_id": str(rec.garment_revision.garment_id),
            "recommended_size": rec.recommended_size,
            "composite_fit_score": float(rec.composite_score),
            "status": exp.get("status", "recommended"),
            "alternative_size": exp.get("alternative_size"),
            "regional_comparisons": exp.get("regional_comparisons", []),
            "disclaimer": exp.get("disclaimer"),
            "rulebook_version": rec.rulebook_version,
            "created_at": rec.created_at.isoformat(),
        }
