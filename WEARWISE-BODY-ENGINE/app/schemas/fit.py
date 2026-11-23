"""
WearWise Honest Fit Recommendation Transport Schemas
"""

from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class FitRecommendRequest(BaseModel):
    """Sizing recommendation query."""
    model_config = ConfigDict(extra="forbid")

    profile_id: UUID
    garment_id: UUID
    user_fit_preference: Literal["tight", "fitted", "regular", "relaxed", "oversized"] = "regular"


class RegionalComparisonResponse(BaseModel):
    region: str
    body_measurement_cm: float
    garment_dimension_cm: float
    ease_cm: float
    classification: str
    explanation: str


class FitRecommendResponse(BaseModel):
    recommendation_id: UUID
    garment_id: UUID
    recommended_size: str
    composite_fit_score: float = Field(..., ge=0.0, le=100.0)
    coverage_ratio: float = Field(..., ge=0.0)
    status: str
    regional_comparisons: List[RegionalComparisonResponse]
    disclaimer: str
