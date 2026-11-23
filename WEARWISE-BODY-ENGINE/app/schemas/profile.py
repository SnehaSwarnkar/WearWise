"""
WearWise Body Profile Transport Schemas
Rejects client-supplied user_id.
"""

from datetime import datetime
from typing import Optional, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.control import ControlsUpdateRequest


class ProfileCreateRequest(BaseModel):
    """Payload to create a new user profile. Client-supplied user_id is strictly forbidden."""
    model_config = ConfigDict(extra="forbid")

    presentation_gender: Literal["masculine", "feminine", "neutral"]
    stature_cm: float = Field(..., ge=100.0, le=230.0, description="Height in cm [100.0, 230.0]")
    reported_weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0, description="Non-apparel metadata")
    initial_controls: Optional[ControlsUpdateRequest] = None


class ProfileUpdateRequest(BaseModel):
    """Payload to update profile metadata."""
    model_config = ConfigDict(extra="forbid")

    presentation_gender: Optional[Literal["masculine", "feminine", "neutral"]] = None
    reported_weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0)


class ProfileResponse(BaseModel):
    profile_id: UUID
    current_revision: int
    presentation_gender: str
    stature_cm: float
    reported_weight_kg: Optional[float] = None
    controls: Dict[str, float]
    latest_avatar_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ProfileRevisionResponse(BaseModel):
    revision_number: int
    created_at: datetime
    measurements_count: int
