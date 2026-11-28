"""
WearWise BICE Semantic-to-Regional Mapping Policy
Versioned, engine-independent mapping from normalized semantic controls [-1.0, 1.0]
to regional 3D shape scaling factors RegionalShapeScale(scale_x, scale_y, scale_z).

Initial engineering hypothesis (v1.0.0-provisional). Zero coupling to 3D avatar engines.
"""

from dataclasses import dataclass
from typing import Dict, Final, Union, Tuple
from app.domain.entities.avatar import RegionalShapeScale
from app.domain.entities.body import BodyShapeControls
from app.bice.config import MAPPING_VERSION
from app.bice.normalizer import normalize_controls
from app.bice.bounds import get_regional_axis_bounds
from app.bice.exceptions import BICEValidationError


@dataclass(frozen=True)
class SemanticMappingRule:
    """Individual rule defining consumer control projection onto regional scale axes."""
    control_name: str
    target_region: str
    primary_axis: str  # "scale_x", "scale_y", "scale_z"
    direction: float   # +1.0 for direct, -1.0 for inverse
    description: str


# Provisional WearWise semantic mapping rules
# Kept centralized, independently testable, and versioned
SEMANTIC_MAPPING_RULES: Final[Dict[str, SemanticMappingRule]] = {
    "shoulder_width": SemanticMappingRule(
        control_name="shoulder_width",
        target_region="shoulders",
        primary_axis="scale_x",
        direction=1.0,
        description="Biacromial lateral breadth scaling (scale_x)",
    ),
    "chest_fullness": SemanticMappingRule(
        control_name="chest_fullness",
        target_region="torso_chest",
        primary_axis="scale_y",
        direction=1.0,
        description="Pectoral/bust anterior depth scaling (scale_y)",
    ),
    "belly_fullness": SemanticMappingRule(
        control_name="belly_fullness",
        target_region="waist_abdomen",
        primary_axis="scale_y",
        direction=1.0,
        description="Abdominal anterior protrusion depth scaling (scale_y)",
    ),
    "waist_definition": SemanticMappingRule(
        control_name="waist_definition",
        target_region="waist_abdomen",
        primary_axis="scale_x",
        direction=-1.0,
        description="Torso lateral taper / indentation scaling (scale_x, inverse)",
    ),
    "arm_fullness": SemanticMappingRule(
        control_name="arm_fullness",
        target_region="arms",
        primary_axis="scale_x",
        direction=1.0,
        description="Arm lateral girth scaling (scale_x)",
    ),
    "hip_fullness": SemanticMappingRule(
        control_name="hip_fullness",
        target_region="hips",
        primary_axis="scale_x",
        direction=1.0,
        description="Pelvic/trochanteric lateral breadth scaling (scale_x)",
    ),
    "thigh_fullness": SemanticMappingRule(
        control_name="thigh_fullness",
        target_region="thighs",
        primary_axis="scale_x",
        direction=1.0,
        description="Upper leg lateral girth scaling (scale_x)",
    ),
    "calf_fullness": SemanticMappingRule(
        control_name="calf_fullness",
        target_region="calves",
        primary_axis="scale_x",
        direction=1.0,
        description="Lower leg gastrocnemius lateral girth scaling (scale_x)",
    ),
}

ALL_TARGET_REGIONS: Final[Tuple[str, ...]] = (
    "shoulders",
    "torso_chest",
    "waist_abdomen",
    "arms",
    "hips",
    "thighs",
    "calves",
)


def map_normalized_to_regional_scales(
    normalized_controls: Dict[str, float],
    mapping_version: str = MAPPING_VERSION,
) -> Dict[str, RegionalShapeScale]:
    """
    Maps normalized controls [-1.0, 1.0] into engine-independent RegionalShapeScale objects.
    All unmapped axes remain at neutral 0.0.
    """
    if mapping_version != MAPPING_VERSION:
        raise BICEValidationError(
            f"Unsupported mapping version '{mapping_version}'. Supported: '{MAPPING_VERSION}'"
        )

    # Initialize all target regions with neutral scale (0.0, 0.0, 0.0)
    region_axes: Dict[str, Dict[str, float]] = {
        region: {"scale_x": 0.0, "scale_y": 0.0, "scale_z": 0.0}
        for region in ALL_TARGET_REGIONS
    }

    # Apply mapping rules scaled to respective regional bounds
    for control_name, rule in SEMANTIC_MAPPING_RULES.items():
        norm_val = normalized_controls.get(control_name, 0.0)
        b_min, b_max, _ = get_regional_axis_bounds(rule.target_region, rule.primary_axis)

        if rule.direction > 0:
            if norm_val >= 0.0:
                target_scale = norm_val * b_max
            else:
                target_scale = norm_val * abs(b_min)
        else:
            # Inverse direction (e.g. waist_definition)
            if norm_val >= 0.0:
                target_scale = -norm_val * abs(b_min)
            else:
                target_scale = -norm_val * b_max

        region_axes[rule.target_region][rule.primary_axis] = target_scale

    return {
        region: RegionalShapeScale(
            scale_x=axes["scale_x"],
            scale_y=axes["scale_y"],
            scale_z=axes["scale_z"],
        )
        for region, axes in region_axes.items()
    }


def map_regional_scales_to_normalized(
    regional_scales: Dict[str, RegionalShapeScale],
    mapping_version: str = MAPPING_VERSION,
) -> Dict[str, float]:
    """
    Inverse projection from RegionalShapeScale back to normalized controls [-1.0, 1.0].
    """
    if mapping_version != MAPPING_VERSION:
        raise BICEValidationError(f"Unsupported mapping version '{mapping_version}'.")

    normalized: Dict[str, float] = {}
    for control_name, rule in SEMANTIC_MAPPING_RULES.items():
        scale_obj = regional_scales.get(
            rule.target_region, RegionalShapeScale(0.0, 0.0, 0.0)
        )
        axis_val = getattr(scale_obj, rule.primary_axis)
        b_min, b_max, _ = get_regional_axis_bounds(rule.target_region, rule.primary_axis)

        if rule.direction > 0:
            if axis_val >= 0.0:
                norm_val = axis_val / b_max if b_max != 0.0 else 0.0
            else:
                norm_val = axis_val / abs(b_min) if b_min != 0.0 else 0.0
        else:
            # Inverse direction
            if axis_val <= 0.0:
                norm_val = -axis_val / abs(b_min) if b_min != 0.0 else 0.0
            else:
                norm_val = -axis_val / b_max if b_max != 0.0 else 0.0

        normalized[control_name] = norm_val

    return normalized


def map_controls_to_regional_scales(
    controls: Union[BodyShapeControls, Dict[str, float]],
    mapping_version: str = MAPPING_VERSION,
) -> Dict[str, RegionalShapeScale]:
    """
    Convenience pipeline: normalizes consumer controls and projects them to regional scales.
    """
    norm = normalize_controls(controls)
    return map_normalized_to_regional_scales(norm, mapping_version=mapping_version)
