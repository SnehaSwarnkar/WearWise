"""
Test Suite: BICE Semantic-to-Regional Mapping Policy
Verifies mapping correctness, bounds scaling, axis isolation, inverse direction for waist definition,
dual-axis waist_abdomen behavior, roundtrip projection, endpoints, and versioning.
"""

import pytest
from app.bice.mapping import (
    SEMANTIC_MAPPING_RULES,
    ALL_TARGET_REGIONS,
    get_regional_axis_bounds,
    map_normalized_to_regional_scales,
    map_regional_scales_to_normalized,
    map_controls_to_regional_scales,
)
from app.bice.bounds import evaluate_regional_bounds, validate_regional_bounds
from app.bice.config import SEMANTIC_CONTROL_SAFE_RANGES
from app.bice.exceptions import BICEValidationError
from app.domain.entities.avatar import RegionalShapeScale
from app.domain.entities.body import BodyShapeControls


@pytest.mark.parametrize("control_name,rule", SEMANTIC_MAPPING_RULES.items())
def test_single_control_axis_isolation(control_name, rule):
    """
    Verify that varying a single control affects ONLY its target region and primary axis.
    All other regions and axes must strictly remain 0.0.
    """
    test_norm_val = 0.65
    reg_scales = map_normalized_to_regional_scales({control_name: test_norm_val})

    min_b, max_b, _ = get_regional_axis_bounds(rule.target_region, rule.primary_axis)
    if rule.direction > 0.0:
        expected_scale = test_norm_val * max_b
    else:
        expected_scale = -test_norm_val * abs(min_b)

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

    # High waist definition (normalized = +1.0) -> negative lateral scale (narrow waist: min bound -1.0)
    scales_high = map_normalized_to_regional_scales({"waist_definition": 1.0})
    assert scales_high["waist_abdomen"].scale_x == pytest.approx(-1.0, abs=1e-5)

    # Low waist definition (normalized = -1.0) -> positive lateral scale (thick waist: max bound +1.0)
    scales_low = map_normalized_to_regional_scales({"waist_definition": -1.0})
    assert scales_low["waist_abdomen"].scale_x == pytest.approx(1.0, abs=1e-5)


def test_waist_abdomen_dual_axis_orthogonality():
    """
    Verify that belly_fullness (scale_y) and waist_definition (scale_x)
    independently and simultaneously modulate waist_abdomen without collision.
    """
    scales = map_normalized_to_regional_scales(
        {"belly_fullness": 0.80, "waist_definition": 0.60}
    )
    # belly_fullness +0.80 * max_b(0.70) = 0.56
    assert scales["waist_abdomen"].scale_y == pytest.approx(0.56, abs=1e-5)
    # waist_definition +0.60 * direction(-1.0) * |min_b(-1.0)| = -0.60
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


@pytest.mark.parametrize("control_name,bounds", SEMANTIC_CONTROL_SAFE_RANGES.items())
def test_control_endpoints_satisfy_regional_bounds(control_name, bounds):
    """
    Verify that for every control at minimum, neutral, and maximum slider values,
    the mapped regional scales strictly satisfy approved regional bounds.
    """
    min_val, max_val = bounds

    # 1. Neutral (0.50)
    neutral_scales = map_controls_to_regional_scales(BodyShapeControls(**{control_name: 0.50}))
    report_neutral = evaluate_regional_bounds(neutral_scales)
    assert report_neutral.is_valid is True
    rule = SEMANTIC_MAPPING_RULES[control_name]
    assert getattr(neutral_scales[rule.target_region], rule.primary_axis) == 0.0

    # 2. Minimum slider value
    min_scales = map_controls_to_regional_scales(BodyShapeControls(**{control_name: min_val}))
    report_min = evaluate_regional_bounds(min_scales)
    assert report_min.is_valid is True, f"Min endpoint violated bounds for {control_name}: {report_min.diagnostics}"

    # 3. Maximum slider value
    max_scales = map_controls_to_regional_scales(BodyShapeControls(**{control_name: max_val}))
    report_max = evaluate_regional_bounds(max_scales)
    assert report_max.is_valid is True, f"Max endpoint violated bounds for {control_name}: {report_max.diagnostics}"


def test_combined_extreme_controls_satisfy_all_regional_bounds():
    """
    Verify that simultaneously modulating all 8 controls to their extremes
    (both all-min and all-max) never generates bounds violations.
    """
    # All minimums
    all_min_kwargs = {c: rng[0] for c, rng in SEMANTIC_CONTROL_SAFE_RANGES.items()}
    scales_min = map_controls_to_regional_scales(BodyShapeControls(**all_min_kwargs))
    report_min = evaluate_regional_bounds(scales_min)
    assert report_min.is_valid is True
    assert report_min.violations_count == 0

    # All maximums
    all_max_kwargs = {c: rng[1] for c, rng in SEMANTIC_CONTROL_SAFE_RANGES.items()}
    scales_max = map_controls_to_regional_scales(BodyShapeControls(**all_max_kwargs))
    report_max = evaluate_regional_bounds(scales_max)
    assert report_max.is_valid is True
    assert report_max.violations_count == 0


def test_unsupported_version():
    """Verify that specifying an unsupported mapping version raises BICEValidationError."""
    with pytest.raises(BICEValidationError):
        map_normalized_to_regional_scales({}, mapping_version="99.9.9")
