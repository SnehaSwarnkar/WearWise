"""
WearWise API Transport Schemas Package
Pydantic v2 request and response contracts strictly separated from domain entities.
"""

from app.schemas.profile import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    ProfileRevisionResponse,
)
from app.schemas.measurement import (
    MeasurementItem,
    MeasurementRecordRequest,
    MeasurementDetailResponse,
    MeasurementRecordResponse,
)
from app.schemas.control import (
    ControlsUpdateRequest,
    ControlsResponse,
)
from app.schemas.avatar import (
    AvatarGenerateRequest,
    AvatarStatusResponse,
)
from app.schemas.garment import (
    FabricPropertiesSchema,
    GarmentMeasurementItem,
    GarmentSizeCreateRequest,
    GarmentCreateRequest,
    GarmentResponse,
)
from app.schemas.fit import (
    FitRecommendRequest,
    RegionalComparisonResponse,
    FitRecommendResponse,
)
from app.schemas.error import (
    ErrorDetail,
    ErrorBody,
    StandardErrorEnvelope,
)

__all__ = [
    "ProfileCreateRequest",
    "ProfileUpdateRequest",
    "ProfileResponse",
    "ProfileRevisionResponse",
    "MeasurementItem",
    "MeasurementRecordRequest",
    "MeasurementDetailResponse",
    "MeasurementRecordResponse",
    "ControlsUpdateRequest",
    "ControlsResponse",
    "AvatarGenerateRequest",
    "AvatarStatusResponse",
    "FabricPropertiesSchema",
    "GarmentMeasurementItem",
    "GarmentSizeCreateRequest",
    "GarmentCreateRequest",
    "GarmentResponse",
    "FitRecommendRequest",
    "RegionalComparisonResponse",
    "FitRecommendResponse",
    "ErrorDetail",
    "ErrorBody",
    "StandardErrorEnvelope",
]
