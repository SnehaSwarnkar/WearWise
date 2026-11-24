"""
WearWise MongoDB Document Repositories
"""

from app.repositories.mongo.profile_repository import MongoProfileRepository
from app.repositories.mongo.avatar_repository import MongoAvatarRepository
from app.repositories.mongo.garment_repository import MongoGarmentRepository
from app.repositories.mongo.fit_repository import MongoFitRepository
from app.repositories.mongo.vton_repository import MongoVTONRepository

__all__ = [
    "MongoProfileRepository",
    "MongoAvatarRepository",
    "MongoGarmentRepository",
    "MongoFitRepository",
    "MongoVTONRepository",
]
