"""
WearWise BICE Semantic and Anthropometric Invariant Validator
Validates consumer semantic controls, body measurements, and presentation morphology
prior to candidate shape specification generation. Rejects anatomically impossible
combinations and enforces strict bounds.
"""

from decimal import Decimal
import math
from typing import Dict, Literal, Optional, Tuple, Union
from app.domain.entities.body import BodyShapeControls, BodyMeasurement
from app.domain.taxonomies.garment import PresentationGender
from app.bice.config import (
    MIN_STATURE_CM,
    MAX_STATURE_CM,
    SEMANTIC_CONTROL_SAFE_RANGES,
    NEUTRAL_CONTROL_VALUE,
)
from app.bice.exceptions import BICEValidationError


VALID_PRESENTATIONS: Tuple[str, ...] = tuple(e.value for e in PresentationGender)


def validate_presentation(presentation: Union[str, PresentationGender]) -> PresentationGender:
    """
    Validates presentation morphology parameter.
    Returns PresentationGender enum.
    """
    if isinstance(presentation, PresentationGender):
        return presentation

    if isinstance(presentation, str):
        try:
            return PresentationGender(presentation)
        except ValueError:
            pass

    raise BICEValidationError(
        f"Invalid presentation morphology '{presentation}'. "
        f"Allowed values are: {list(VALID_PRESENTATIONS)}"
    )


def validate_stature(stature_cm: Union[float, Decimal, int]) -> float:
    """
    Validates stature measurement in centimeters against standard anthropometric bounds.
    """
    if not isinstance(stature_cm, (int, float, Decimal)) or isinstance(stature_cm, bool):
        raise BICEValidationError(
            f"Stature must be numeric, got {type(stature_cm).__name__}."
        )

    val = float(stature_cm)
    if math.isnan(val) or math.isinf(val):
        raise BICEValidationError(f"Stature value cannot be non-finite ({val}).")

    if val < MIN_STATURE_CM or val > MAX_STATURE_CM:
        raise BICEValidationError(
            f"Stature {val:.2f} cm is outside valid anthropometric range "
            f"[{MIN_STATURE_CM:.1f}, {MAX_STATURE_CM:.1f}] cm."
        )

    return val


def validate_controls_input(
    controls: Union[BodyShapeControls, Dict[str, float]]
) -> Dict[str, float]:
    """
    Validates consumer semantic controls against control-specific safe ranges.
    Rejects non-finite values and out-of-range values without silent clamping.
    """
    if isinstance(controls, BodyShapeControls):
        ctrl_dict = controls.to_dict()
    elif isinstance(controls, dict):
        ctrl_dict = controls
    else:
        raise BICEValidationError(
            f"Expected BodyShapeControls or dict for controls, got {type(controls).__name__}"
        )

    validated: Dict[str, float] = {}
    for name, (min_val, max_val) in SEMANTIC_CONTROL_SAFE_RANGES.items():
        val = ctrl_dict.get(name, NEUTRAL_CONTROL_VALUE)
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise BICEValidationError(
                f"Control '{name}' must be numeric, got {type(val).__name__}."
            )
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            raise BICEValidationError(f"Control '{name}' cannot be non-finite ({val}).")
        if f_val < min_val or f_val > max_val:
            raise BICEValidationError(
                f"Control '{name}' value {f_val} is out of safe range [{min_val}, {max_val}]."
            )
        validated[name] = f_val

    return validated


def validate_measurements_input(
    measurements: Union[Dict[str, BodyMeasurement], Dict[str, Union[float, Decimal]]]
) -> Dict[str, float]:
    """
    Validates physical body measurements in centimeters and checks anatomical plausibility.
    """
    if not isinstance(measurements, dict):
        raise BICEValidationError(
            f"Expected dict for measurements, got {type(measurements).__name__}"
        )

    validated: Dict[str, float] = {}

    for code, m in measurements.items():
        if isinstance(m, BodyMeasurement):
            val = float(m.value_cm)
            if m.unit != "cm":
                raise BICEValidationError(f"Measurement '{code}' unit must be 'cm', got '{m.unit}'")
        elif isinstance(m, (int, float, Decimal)) and not isinstance(m, bool):
            val = float(m)
        else:
            raise BICEValidationError(
                f"Measurement '{code}' must be BodyMeasurement or numeric, got {type(m).__name__}"
            )

        if math.isnan(val) or math.isinf(val) or val <= 0.0:
            raise BICEValidationError(
                f"Measurement '{code}' value must be positive finite, got {val}"
            )

        validated[code] = val

    # Validate stature if present
    if "stature" in validated:
        validate_stature(validated["stature"])

    # Anatomical consistency cross-checks
    chest = validated.get("chest_circumference")
    waist = validated.get("waist_circumference")
    hip = validated.get("hip_circumference")
    stature = validated.get("stature")

    # Circumference bounds [30.0, 220.0] cm
    for name, c_val in [("chest", chest), ("waist", waist), ("hip", hip)]:
        if c_val is not None:
            if c_val < 30.0 or c_val > 220.0:
                raise BICEValidationError(
                    f"Anatomically implausible {name} circumference: {c_val:.2f} cm (expected [30.0, 220.0] cm)."
                )

    # Implausible proportions check
    if stature is not None and chest is not None:
        if chest > stature * 1.5:
            raise BICEValidationError(
                f"Anatomically implausible: chest circumference ({chest:.1f} cm) "
                f"exceeds 150% of stature ({stature:.1f} cm)."
            )

    if waist is not None and hip is not None:
        if waist > hip * 2.5:
            raise BICEValidationError(
                f"Anatomically implausible: waist circumference ({waist:.1f} cm) "
                f"exceeds 250% of hip circumference ({hip:.1f} cm)."
            )

    return validated
