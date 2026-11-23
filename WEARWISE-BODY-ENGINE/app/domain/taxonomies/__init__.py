"""
WearWise Domain Taxonomies
"""

from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import (
    PresentationGender,
    FabricStretchDirection,
    RegionalFitClassification,
)

__all__ = [
    "MeasurementAcquisitionMethod",
    "MeasurementValidationState",
    "MeasurementLifecycleStatus",
    "MeasurementAssessmentState",
    "PresentationGender",
    "FabricStretchDirection",
    "RegionalFitClassification",
]
