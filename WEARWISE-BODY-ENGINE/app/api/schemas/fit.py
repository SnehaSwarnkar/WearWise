"""
Pydantic Schemas for Honest Fit Recommendation
"""

from typing import Dict, List, Any, Optional
import uuid
from pydantic import BaseModel, Field


class FitRecommendationRequest(BaseModel):
    profile_id: uuid.UUID
    garment_id: uuid.UUID
    user_fit_preference: str = Field("regular", pattern="^(fitted|regular|loose|relaxed)$")


class RegionalComparisonItem(BaseModel):
    region: str
    body_measurement_cm: float
    garment_dimension_cm: float
    ease_cm: float
    classification: str
    explanation: str


class FitRecommendationResponse(BaseModel):
    recommendation_id: str
    garment_id: str
    recommended_size: str
    composite_fit_score: float
    status: str
    alternative_size: Optional[Dict[str, Any]] = None
    regional_comparisons: List[RegionalComparisonItem]
    disclaimer: str
