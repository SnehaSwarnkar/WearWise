"""
WearWise Body Shape Controls Transport Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ControlsUpdateRequest(BaseModel):
    """Semantic slider updates with control-specific safe ranges. Extra fields forbidden."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    shoulder_width: Optional[float] = Field(None, ge=0.10, le=0.90)
    chest_fullness: Optional[float] = Field(None, ge=0.10, le=0.90)
    belly_fullness: Optional[float] = Field(None, ge=0.10, le=0.85)
    waist_definition: Optional[float] = Field(None, ge=0.15, le=0.85)
    arm_fullness: Optional[float] = Field(None, ge=0.10, le=0.90)
    hip_fullness: Optional[float] = Field(None, ge=0.15, le=0.85)
    thigh_fullness: Optional[float] = Field(None, ge=0.20, le=0.80)
    calf_fullness: Optional[float] = Field(None, ge=0.15, le=0.85)


class ControlsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    shoulder_width: float = Field(..., ge=0.10, le=0.90)
    chest_fullness: float = Field(..., ge=0.10, le=0.90)
    belly_fullness: float = Field(..., ge=0.10, le=0.85)
    waist_definition: float = Field(..., ge=0.15, le=0.85)
    arm_fullness: float = Field(..., ge=0.10, le=0.90)
    hip_fullness: float = Field(..., ge=0.15, le=0.85)
    thigh_fullness: float = Field(..., ge=0.20, le=0.80)
    calf_fullness: float = Field(..., ge=0.15, le=0.85)
