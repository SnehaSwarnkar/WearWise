"""
WearWise Body Shape Controls Transport Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ControlsUpdateRequest(BaseModel):
    """Semantic slider updates with strict bounds [0.0, 1.0]. Extra fields forbidden."""
    model_config = ConfigDict(extra="forbid")

    shoulder_width: Optional[float] = Field(None, ge=0.0, le=1.0)
    chest_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)
    belly_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)
    waist_definition: Optional[float] = Field(None, ge=0.0, le=1.0)
    arm_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)
    hip_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)
    thigh_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)
    calf_fullness: Optional[float] = Field(None, ge=0.0, le=1.0)


class ControlsResponse(BaseModel):
    shoulder_width: float
    chest_fullness: float
    belly_fullness: float
    waist_definition: float
    arm_fullness: float
    hip_fullness: float
    thigh_fullness: float
    calf_fullness: float
