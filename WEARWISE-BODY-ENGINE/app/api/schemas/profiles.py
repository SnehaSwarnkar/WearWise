"""
Pydantic Schemas for Body Profiles & Measurements
Conforms strictly to API_CONTRACTS.md Rev 1.2.1.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid
from pydantic import BaseModel, Field


class InitialControls(BaseModel):
    shoulder_width: float = Field(0.50, ge=0.0, le=1.0)
    chest_fullness: float = Field(0.50, ge=0.0, le=1.0)
    belly_fullness: float = Field(0.50, ge=0.0, le=1.0)
    waist_definition: float = Field(0.50, ge=0.0, le=1.0)
    arm_fullness: float = Field(0.50, ge=0.0, le=1.0)
    hip_fullness: float = Field(0.50, ge=0.0, le=1.0)
    thigh_fullness: float = Field(0.50, ge=0.0, le=1.0)
    calf_fullness: float = Field(0.50, ge=0.0, le=1.0)


class CreateProfileRequest(BaseModel):
    presentation_gender: str = Field(..., pattern="^(masculine|feminine|neutral)$")
    stature_cm: float = Field(..., ge=100.0, le=230.0)
    reported_weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0)
    avatar_name: Optional[str] = Field(None, max_length=80)
    body_shape: Optional[str] = Field(None, max_length=48)
    age_range: Optional[str] = Field(None, max_length=32)
    initial_controls: Optional[Dict[str, float]] = None


class UpdateProfileRequest(BaseModel):
    presentation_gender: Optional[str] = Field(None, pattern="^(masculine|feminine|neutral)$")
    stature_cm: Optional[float] = Field(None, ge=100.0, le=230.0)
    reported_weight_kg: Optional[float] = Field(None, ge=30.0, le=300.0)
    avatar_name: Optional[str] = Field(None, max_length=80)
    body_shape: Optional[str] = Field(None, max_length=48)
    age_range: Optional[str] = Field(None, max_length=32)


class MeasurementItem(BaseModel):
    measurement_code: str
    value_cm: float = Field(..., gt=0.0)
    unit: str = Field("cm", pattern="^cm$")
    acquisition_method: str = "tape_measured"
    tolerance_cm: float = 1.00
    landmark_convention: str = "standard_landmark"


class RecordMeasurementsRequest(BaseModel):
    expected_revision: int
    measurements: List[MeasurementItem]


class UpdateControlsRequest(BaseModel):
    expected_revision: int
    controls: Dict[str, float]


class ProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    current_revision: int
    avatar_name: Optional[str] = None
    body_shape: Optional[str] = None
    age_range: Optional[str] = None
    presentation_gender: str
    stature_cm: float
    reported_weight_kg: Optional[float]
    active_measurements: Dict[str, Any]
    shape_controls: Dict[str, float]
    latest_asset_url: Optional[str] = None
    created_at: str
    updated_at: str
