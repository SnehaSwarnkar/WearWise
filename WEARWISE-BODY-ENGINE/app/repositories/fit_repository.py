"""
WearWise Fit Repository
Persists and retrieves Honest Fit recommendation evaluation results.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import FitRecommendationModel


class FitRepository:
    """Repository for Honest Fit recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def save_fit_recommendation(
        self,
        profile_revision_id: uuid.UUID,
        garment_revision_id: uuid.UUID,
        recommended_size: str,
        composite_score: Decimal,
        explanations_json: Dict[str, Any],
        rulebook_version: str,
    ) -> FitRecommendationModel:
        """Persists a computed fit recommendation."""
        rec = FitRecommendationModel(
            profile_revision_id=profile_revision_id,
            garment_revision_id=garment_revision_id,
            recommended_size=recommended_size,
            composite_score=composite_score,
            explanations_json=explanations_json,
            rulebook_version=rulebook_version,
        )
        self.db.add(rec)
        self.db.flush()
        return rec

    def get_fit_recommendation(self, recommendation_id: uuid.UUID) -> Optional[FitRecommendationModel]:
        """Retrieves recommendation by id with related profile and garment revisions."""
        stmt = (
            select(FitRecommendationModel)
            .where(FitRecommendationModel.id == recommendation_id)
            .options(
                joinedload(FitRecommendationModel.profile_revision),
                joinedload(FitRecommendationModel.garment_revision),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_recent_recommendations_for_profile(self, profile_id: uuid.UUID, limit: int = 10):
        """Lists recent fit recommendations for a given profile."""
        from app.db.models import ProfileRevisionModel
        stmt = (
            select(FitRecommendationModel)
            .join(ProfileRevisionModel, ProfileRevisionModel.id == FitRecommendationModel.profile_revision_id)
            .where(ProfileRevisionModel.profile_id == profile_id)
            .options(
                joinedload(FitRecommendationModel.profile_revision),
                joinedload(FitRecommendationModel.garment_revision),
            )
            .order_by(FitRecommendationModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())
