"""
WearWise Honest Fit Package
Transparent dimensional ease comparison and fit recommendations.
"""

from app.fit.rulebook import (
    EASE_RULEBOOK,
    BASELINE_REGIONAL_WEIGHTS,
    DEFAULT_BETA_COEFFICIENTS,
    MINIMUM_WEARABLE_EASE,
    RULEBOOK_VERSION,
)
from app.fit.registry import (
    MeasurementCompatibilityRegistry,
    DimensionTransformation,
)
from app.fit.models import (
    RegionalFitResult,
    FitEvaluationReport,
    GarmentInputSpec,
    GarmentMeasurementProvenance,
)
from app.fit.engine import HonestFitEngine
from app.fit.port import HonestFitEvaluationPort

__all__ = [
    "EASE_RULEBOOK",
    "BASELINE_REGIONAL_WEIGHTS",
    "DEFAULT_BETA_COEFFICIENTS",
    "MINIMUM_WEARABLE_EASE",
    "RULEBOOK_VERSION",
    "MeasurementCompatibilityRegistry",
    "DimensionTransformation",
    "RegionalFitResult",
    "FitEvaluationReport",
    "GarmentInputSpec",
    "GarmentMeasurementProvenance",
    "HonestFitEngine",
    "HonestFitEvaluationPort",
]
