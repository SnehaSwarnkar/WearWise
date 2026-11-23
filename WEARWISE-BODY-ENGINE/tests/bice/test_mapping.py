"""
Test Suite: BICE Semantic-to-Regional Mapping Policy
Verifies mapping correctness, axis isolation, inverse direction for waist definition,
dual-axis waist_abdomen behavior, roundtrip projection, and versioning.
"""

import pytest
from app.bice.mapping import (
    SEMANTIC_MAPPING_RULES,
    ALL_TARGET_REGIONS,
    map_normalized_to_regional_scales,
    map_regional_scales_to_normalized,
    map_controls_to_regional_scales,
)
from app.bice.exceptions import BICEValidationError
from app.domain.entities.avatar import RegionalShapeScale


@pytest.mark.parametrize("control_name,rule", SEMANTIC_MAPPING_RULES.items())
def test_single_control_axis_isolation(control_name, rule):
    """
    Verify that varying a single control affects ONLY its target region and primary axis.
    All other regions and axes must strictly remain 0.0.
    """
    test_norm_val = 0.65
    reg_scales = map_normalized_to_regional_scales({control_name: test_norm_val})

    expected_scale = test_norm_val * rule.direction

    for region_name, scale in reg_scales.items():
        if region_name == rule.target_region:
            for axis in ("scale_x", "scale_y", "scale_z"):
                actual_val = getattr(scale, axis)
                if axis == rule.primary_axis:
                    assert actual_val == pytest.approx(expected_scale, abs=1e-5)
                else:
                    assert actual_val == 0.0
        else:
            assert scale.scale_x == 0.0
            assert scale.scale_y == 0.0
            assert scale.scale_z == 0.0


def test_waist_definition_inverse_direction():
    """Verify waist_definition maps to scale_x in waist_abdomen with inverse direction."""
    rule = SEMANTIC_MAPPING_RULES["waist_definition"]
    assert rule.target_region == "waist_abdomen"
    assert rule.primary_axis == "scale_x"
    assert rule.direction == -1.0

    # High waist definition (normalized = +1.0) -> negative lateral scale (narrow waist)
    scales_high = map_normalized_to_regional_scales({"waist_definition": 1.0})
    assert scales_high["waist_abdomen"].scale_x == -1.0

    # Low waist definition (normalized = -1.0) -> positive lateral scale (thick waist)
    scales_low = map_normalized_to_regional_scales({"waist_definition": -1.0})
    assert scales_low["waist_abdomen"].scale_x == 1.0


def test_waist_abdomen_dual_axis_orthogonality():
    """
    Verify that belly_fullness (scale_y) and waist_definition (scale_x)
    independently and simultaneously modulate waist_abdomen without collision.
    """
    scales = map_normalized_to_regional_scales(
        {"belly_fullness": 0.80, "waist_definition": 0.60}
    )
    assert scales["waist_abdomen"].scale_y == pytest.approx(0.80, abs=1e-5)
    assert scales["waist_abdomen"].scale_x == pytest.approx(-0.60, abs=1e-5)
    assert scales["waist_abdomen"].scale_z == 0.0


def test_mapping_roundtrip():
    """Verify roundtrip mapping from normalized controls to regional scales and back."""
    norm_input = {
        "shoulder_width": 0.40,
        "chest_fullness": -0.50,
        "belly_fullness": 0.35,
        "waist_definition": -0.20,
        "arm_fullness": 0.70,
        "hip_fullness": -0.80,
        "thigh_fullness": 0.15,
        "calf_fullness": -0.25,
    }
    scales = map_normalized_to_regional_scales(norm_input)
    recovered = map_regional_scales_to_normalized(scales)

    for k, v in norm_input.items():
        assert recovered[k] == pytest.approx(v, abs=1e-5)


def test_unsupported_version():
    """Verify that specifying an unsupported mapping version raises BICEValidationError."""
    with pytest.raises(BICEValidationError):
        map_normalized_to_regional_scales({}, mapping_version="99.9.9")
