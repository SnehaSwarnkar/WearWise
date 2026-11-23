"""
WearWise Honest Fit Provisional Ease Rulebook
Defines 6-tier non-overlapping intervals [a, b), baseline weights, and provisional thresholds.
"""

from typing import Dict, Tuple
from app.domain.taxonomies.garment import RegionalFitClassification

RULEBOOK_VERSION = "1.2.1-provisional"

# 6-tier non-overlapping intervals [low, high) per dimension
# Float inf used for unbounded endpoints
INF = float("inf")

PROVISIONAL_EASE_INTERVALS: Dict[str, Dict[RegionalFitClassification, Tuple[float, float]]] = {
    "chest_circumference": {
        RegionalFitClassification.TOO_TIGHT: (-INF, 2.0),
        RegionalFitClassification.FITTED: (2.0, 6.0),
        RegionalFitClassification.REGULAR: (6.0, 12.0),
        RegionalFitClassification.RELAXED: (12.0, 18.0),
        RegionalFitClassification.OVERSIZED: (18.0, 24.0),
        RegionalFitClassification.TOO_LARGE: (24.0, INF),
    },
    "waist_planar_circumference": {
        RegionalFitClassification.TOO_TIGHT: (-INF, 2.0),
        RegionalFitClassification.FITTED: (2.0, 6.0),
        RegionalFitClassification.REGULAR: (6.0, 12.0),
        RegionalFitClassification.RELAXED: (12.0, 18.0),
        RegionalFitClassification.OVERSIZED: (18.0, 24.0),
        RegionalFitClassification.TOO_LARGE: (24.0, INF),
    },
    "shoulder_biacromial_breadth": {
        RegionalFitClassification.TOO_TIGHT: (-INF, -1.0),
        RegionalFitClassification.FITTED: (-1.0, 1.5),
        RegionalFitClassification.REGULAR: (1.5, 3.5),
        RegionalFitClassification.RELAXED: (3.5, 6.0),
        RegionalFitClassification.OVERSIZED: (6.0, 9.0),
        RegionalFitClassification.TOO_LARGE: (9.0, INF),
    },
    "torso_length": {
        RegionalFitClassification.TOO_TIGHT: (-INF, -4.0),
        RegionalFitClassification.FITTED: (-4.0, 0.0),
        RegionalFitClassification.REGULAR: (0.0, 6.0),
        RegionalFitClassification.RELAXED: (6.0, 12.0),
        RegionalFitClassification.OVERSIZED: (12.0, 18.0),
        RegionalFitClassification.TOO_LARGE: (18.0, INF),
    },
    "hip_circumference": {
        RegionalFitClassification.TOO_TIGHT: (-INF, 3.0),
        RegionalFitClassification.FITTED: (3.0, 7.0),
        RegionalFitClassification.REGULAR: (7.0, 13.0),
        RegionalFitClassification.RELAXED: (13.0, 19.0),
        RegionalFitClassification.OVERSIZED: (19.0, 25.0),
        RegionalFitClassification.TOO_LARGE: (25.0, INF),
    },
    "leg_thigh_circumference": {
        RegionalFitClassification.TOO_TIGHT: (-INF, 2.0),
        RegionalFitClassification.FITTED: (2.0, 5.0),
        RegionalFitClassification.REGULAR: (5.0, 9.0),
        RegionalFitClassification.RELAXED: (9.0, 14.0),
        RegionalFitClassification.OVERSIZED: (14.0, 19.0),
        RegionalFitClassification.TOO_LARGE: (19.0, INF),
    },
}

# Alias for backwards and spec compatibility
EASE_RULEBOOK = PROVISIONAL_EASE_INTERVALS

# Minimum wearable ease for rigid fabrics (Ease < min => unwearable, penalty=100)
MINIMUM_WEARABLE_EASE: Dict[str, float] = {
    "chest_circumference": 2.0,
    "waist_planar_circumference": 2.0,
    "shoulder_biacromial_breadth": -1.0,
    "torso_length": -4.0,
    "hip_circumference": 3.0,
    "leg_thigh_circumference": 2.0,
}

# Baseline importance weights per garment category
BASELINE_REGIONAL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "t_shirt": {
        "chest_circumference": 0.40,
        "shoulder_biacromial_breadth": 0.30,
        "torso_length": 0.10,
        "waist_planar_circumference": 0.20,
    },
    "polo": {
        "chest_circumference": 0.40,
        "shoulder_biacromial_breadth": 0.30,
        "torso_length": 0.10,
        "waist_planar_circumference": 0.20,
    },
    "casual_shirt": {
        "chest_circumference": 0.40,
        "shoulder_biacromial_breadth": 0.30,
        "waist_planar_circumference": 0.20,
        "torso_length": 0.10,
    },
    "dress_shirt": {
        "chest_circumference": 0.40,
        "shoulder_biacromial_breadth": 0.30,
        "waist_planar_circumference": 0.20,
        "torso_length": 0.10,
    },
    "trousers": {
        "waist_planar_circumference": 0.40,
        "hip_circumference": 0.40,
        "leg_thigh_circumference": 0.20,
    },
    "jeans": {
        "waist_planar_circumference": 0.40,
        "hip_circumference": 0.40,
        "leg_thigh_circumference": 0.20,
    },
}

# Default proposed provisional beta penalty coefficients (cm^-2)
DEFAULT_BETA_COEFFICIENTS: Dict[str, float] = {
    "chest_circumference": 2.0,
    "shoulder_biacromial_breadth": 12.0,
    "waist_planar_circumference": 2.0,
    "torso_length": 2.0,
    "hip_circumference": 2.0,
    "leg_thigh_circumference": 2.0,
}
