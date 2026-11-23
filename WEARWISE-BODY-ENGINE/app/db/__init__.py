"""
WearWise Persistence Package
"""

from app.db.base import Base
from app.db.session import engine, SessionFactory, init_db, get_db
from app.db.models import (
    BodyProfileModel,
    ProfileRevisionModel,
    BodyMeasurementModel,
    BodyShapeControlsModel,
    AvatarConfigurationModel,
    AvatarAssetModel,
    GarmentProfileModel,
    GarmentRevisionModel,
    GarmentSizeModel,
    GarmentMeasurementModel,
    FitRecommendationModel,
    AssetDeletionOutboxModel,
)

__all__ = [
    "Base",
    "engine",
    "SessionFactory",
    "init_db",
    "get_db",
    "BodyProfileModel",
    "ProfileRevisionModel",
    "BodyMeasurementModel",
    "BodyShapeControlsModel",
    "AvatarConfigurationModel",
    "AvatarAssetModel",
    "GarmentProfileModel",
    "GarmentRevisionModel",
    "GarmentSizeModel",
    "GarmentMeasurementModel",
    "FitRecommendationModel",
    "AssetDeletionOutboxModel",
]
