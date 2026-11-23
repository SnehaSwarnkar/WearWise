"""
FastAPI Router for Honest Fit Recommendations
Endpoint base: /api/v1/fit
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_user_id
from app.services.fit_service import FitEvaluationService
from app.api.schemas.fit import (
    FitRecommendationRequest,
    FitRecommendationResponse,
)

router = APIRouter(prefix="/fit", tags=["Honest Fit Recommendation"])


@router.post("/recommend", response_model=FitRecommendationResponse)
def evaluate_fit(
    payload: FitRecommendationRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Evaluates active profile measurements against garment size dimensions
    using the approved Phase 5A Honest Fit Engine and persists recommendation.
    """
    srv = FitEvaluationService(db)
    result = srv.evaluate_fit(
        profile_id=payload.profile_id,
        garment_id=payload.garment_id,
        user_preference=payload.user_fit_preference,
        requesting_user_id=user_id,
    )
    db.commit()
    return result


@router.get("/recommendations/{recommendation_id}")
def get_recommendation(
    recommendation_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves persisted fit recommendation result after verifying ownership."""
    srv = FitEvaluationService(db)
    return srv.get_recommendation(
        recommendation_id=recommendation_id,
        requesting_user_id=user_id,
    )
