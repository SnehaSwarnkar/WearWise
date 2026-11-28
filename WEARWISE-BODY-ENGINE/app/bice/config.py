"""
WearWise BICE Configuration Module
Centralized, immutable configuration for normalizer, regional bounds, and locality parameters.
All regional bounds are explicitly tagged with provisional engineering notices.
"""

from typing import Dict, Tuple, Final
from app.domain.entities.body import CONTROL_SAFE_RANGES

# Specifications and versions
BICE_SPEC_VERSION: Final[str] = "1.2.1"
MAPPING_VERSION: Final[str] = "1.0.0-provisional"
METRIC_VERSION: Final[str] = "1.2.1-rmsr-pvsr"

# Normalization constants
NEUTRAL_CONTROL_VALUE: Final[float] = 0.50
NEUTRAL_NORMALIZED_OFFSET: Final[float] = 0.0

# Stature bounds in cm
MIN_STATURE_CM: Final[float] = 100.0
MAX_STATURE_CM: Final[float] = 230.0

# Consumer semantic control safe ranges (matching Phase 1 & 2.1 specifications)
# Re-exported from domain entity for single source of truth
SEMANTIC_CONTROL_SAFE_RANGES: Final[Dict[str, Tuple[float, float]]] = dict(CONTROL_SAFE_RANGES)

# Provisional regional engineering limits
# These protect anatomical integrity pending Phase 4 mesh validity integration:
# - thighs scale_x in [-0.50, +0.50] (prevents severe pelvic/groin RMSR leakage of 4.04)
# - waist_abdomen scale_y in [-0.50, +0.70] (prevents excessive anterior rib flare)
# - shoulders scale_x in [-0.75, +0.75] (protects clavicle mesh smoothness)
# General fallback bound is [-1.0, +1.0]
IS_PROVISIONAL_BOUNDS: Final[bool] = True
BOUNDS_PROVISIONAL_NOTICE: Final[str] = (
    "Provisional engineering bounds applied pending Phase 4 mesh validity integration."
)

PROVISIONAL_REGIONAL_BOUNDS: Final[Dict[str, Dict[str, Tuple[float, float]]]] = {
    "thighs": {
        "scale_x": (-0.50, 0.50),
    },
    "waist_abdomen": {
        "scale_y": (-0.50, 0.70),
    },
    "shoulders": {
        "scale_x": (-0.75, 0.75),
    },
}

DEFAULT_REGIONAL_BOUNDS: Final[Tuple[float, float]] = (-1.0, 1.0)

# Locality evaluation parameters
TARGET_SIGNAL_THRESHOLD_M: Final[float] = 1e-4  # 0.1 mm in meters
MAXIMAL_LOCALITY_PENALTY: Final[float] = 10.0
