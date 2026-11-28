"""
WearWise Body Measurement Transport Schemas
"""

from datetime import datetime
from typing import List, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class MeasurementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measurement_code: str
    value_cm: float = Field(..., gt=0.0)
    unit: Literal["cm"] = "cm"
    acquisition_method: Literal["user_reported", "tape_measured", "geometry_extracted", "model_estimated"] = "tape_measured"
    tolerance_cm: float = Field(1.00, ge=0.0)
    landmark_convention: str = "standard_landmark"


class MeasurementRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(..., ge=1)
    measurements: List[MeasurementItem] = Field(..., min_length=1)


class MeasurementDetailResponse(BaseModel):
    measurement_code: str
    value_cm: float
    unit: str
    acquisition_method: str
    validation_state: str
    lifecycle_status: str
    assessment_state: str
    tolerance_cm: float
    reliability_weight: float
    captured_at: datetime


class MeasurementRecordResponse(BaseModel):
    profile_id: UUID
    new_revision: int
    recorded_count: int
    active_measurements: Dict[str, MeasurementDetailResponse]
