"""
WearWise BICE Semantic Normalizer
Deterministic normalization of semantic consumer controls [0.0, 1.0] to centered offsets [-1.0, 1.0].
Neutral baseline 0.50 maps strictly to 0.0.
"""

import math
from typing import Dict, Union
from app.domain.entities.body import BodyShapeControls
from app.bice.config import (
    SEMANTIC_CONTROL_SAFE_RANGES,
    NEUTRAL_CONTROL_VALUE,
    NEUTRAL_NORMALIZED_OFFSET,
)
from app.bice.exceptions import BICEValidationError


def normalize_control(control_name: str, value: float) -> float:
    """
    Normalizes a single semantic control value to a centered offset [-1.0, 1.0].
    
    Invariant guarantees:
    - Neutral 0.50 -> 0.0 strictly.
    - Min safe bound -> -1.0 strictly.
    - Max safe bound -> +1.0 strictly.
    - Strictly monotonic response for all inputs within the safe range.
    - Rejects invalid, out-of-range, and non-finite inputs without silent clamping.
    """
    if control_name not in SEMANTIC_CONTROL_SAFE_RANGES:
        raise BICEValidationError(
            f"Unknown semantic control name: '{control_name}'. "
            f"Valid controls are: {list(SEMANTIC_CONTROL_SAFE_RANGES.keys())}"
        )

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise BICEValidationError(
            f"Control '{control_name}' value must be numeric, got {type(value).__name__}."
        )

    if math.isnan(value) or math.isinf(value):
        raise BICEValidationError(
            f"Control '{control_name}' value cannot be non-finite ({value})."
        )

    min_val, max_val = SEMANTIC_CONTROL_SAFE_RANGES[control_name]
    if value < min_val or value > max_val:
        raise BICEValidationError(
            f"Control '{control_name}' value {value} is out of safe range [{min_val}, {max_val}]."
        )

    if value == NEUTRAL_CONTROL_VALUE:
        return NEUTRAL_NORMALIZED_OFFSET

    if value > NEUTRAL_CONTROL_VALUE:
        return (value - NEUTRAL_CONTROL_VALUE) / (max_val - NEUTRAL_CONTROL_VALUE)
    else:
        return (value - NEUTRAL_CONTROL_VALUE) / (NEUTRAL_CONTROL_VALUE - min_val)


def denormalize_control(control_name: str, normalized_val: float) -> float:
    """
    Inverts a normalized offset [-1.0, 1.0] back to the consumer control space.
    """
    if control_name not in SEMANTIC_CONTROL_SAFE_RANGES:
        raise BICEValidationError(f"Unknown semantic control name: '{control_name}'")

    if not isinstance(normalized_val, (int, float)) or isinstance(normalized_val, bool):
        raise BICEValidationError("Normalized value must be numeric.")

    if math.isnan(normalized_val) or math.isinf(normalized_val):
        raise BICEValidationError(f"Normalized value cannot be non-finite ({normalized_val}).")

    if normalized_val < -1.0 or normalized_val > 1.0:
        raise BICEValidationError(
            f"Normalized value {normalized_val} out of normalized bounds [-1.0, 1.0]."
        )

    min_val, max_val = SEMANTIC_CONTROL_SAFE_RANGES[control_name]
    if normalized_val == 0.0:
        return NEUTRAL_CONTROL_VALUE

    if normalized_val > 0.0:
        raw = NEUTRAL_CONTROL_VALUE + normalized_val * (max_val - NEUTRAL_CONTROL_VALUE)
    else:
        raw = NEUTRAL_CONTROL_VALUE + normalized_val * (NEUTRAL_CONTROL_VALUE - min_val)

    return round(raw, 4)


def normalize_controls(
    controls: Union[BodyShapeControls, Dict[str, float]]
) -> Dict[str, float]:
    """
    Normalizes all eight semantic controls into centered offsets [-1.0, 1.0].
    """
    if isinstance(controls, BodyShapeControls):
        ctrl_dict = controls.to_dict()
    elif isinstance(controls, dict):
        ctrl_dict = controls
    else:
        raise BICEValidationError(
            f"Expected BodyShapeControls or dict, got {type(controls).__name__}"
        )

    normalized = {}
    for name in SEMANTIC_CONTROL_SAFE_RANGES:
        val = ctrl_dict.get(name, NEUTRAL_CONTROL_VALUE)
        normalized[name] = normalize_control(name, val)

    return normalized


def denormalize_controls(normalized_controls: Dict[str, float]) -> BodyShapeControls:
    """
    Constructs a validated BodyShapeControls domain entity from normalized offsets.
    """
    raw_dict = {}
    for name in SEMANTIC_CONTROL_SAFE_RANGES:
        norm_val = normalized_controls.get(name, 0.0)
        raw_dict[name] = denormalize_control(name, norm_val)

    return BodyShapeControls(**raw_dict)
