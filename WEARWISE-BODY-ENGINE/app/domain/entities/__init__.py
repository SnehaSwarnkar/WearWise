"""
WearWise Domain Entities Package
Canonical, framework-independent domain models and value objects.
"""

from app.domain.entities.body import (
    BodyProfile,
    ProfileRevision,
    BodyMeasurement,
    BodyShapeControls,
)
from app.domain.entities.avatar import (
    RegionalShapeScale,
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    RegionalDisplacementSummary,
    ShapeEvaluationResult,
)
from app.domain.entities.garment import (
    FabricProperties,
    GarmentProfile,
    GarmentRevision,
    GarmentSize,
    GarmentMeasurement,
    RegionalFitEvaluation,
    FitRecommendation,
)

__all__ = [
    "BodyProfile",
    "ProfileRevision",
    "BodyMeasurement",
    "BodyShapeControls",
    "RegionalShapeScale",
    "AvatarShapeSpec",
    "MeshData",
    "LandmarkData",
    "RegionalDisplacementSummary",
    "ShapeEvaluationResult",
    "FabricProperties",
    "GarmentProfile",
    "GarmentRevision",
    "GarmentSize",
    "GarmentMeasurement",
    "RegionalFitEvaluation",
    "FitRecommendation",
]
