"""
WearWise API Schemas Package
"""

from app.api.schemas.profiles import (
    CreateProfileRequest,
    UpdateProfileRequest,
    RecordMeasurementsRequest,
    UpdateControlsRequest,
    ProfileResponse,
)
from app.api.schemas.avatar import (
    GenerateAvatarRequest,
    AvatarGenerationResponse,
    AvatarStatusResponse,
)
from app.api.schemas.garment import (
    CreateGarmentRequest,
    AddGarmentSizeRequest,
    GarmentResponse,
)
from app.api.schemas.fit import (
    FitRecommendationRequest,
    FitRecommendationResponse,
)

__all__ = [
    "CreateProfileRequest",
    "UpdateProfileRequest",
    "RecordMeasurementsRequest",
    "UpdateControlsRequest",
    "ProfileResponse",
    "GenerateAvatarRequest",
    "AvatarGenerationResponse",
    "AvatarStatusResponse",
    "CreateGarmentRequest",
    "AddGarmentSizeRequest",
    "GarmentResponse",
    "FitRecommendationRequest",
    "FitRecommendationResponse",
]
