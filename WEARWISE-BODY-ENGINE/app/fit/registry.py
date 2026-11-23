"""
WearWise Measurement Compatibility Registry
Maps garment dimension codes to canonical body measurement codes with transformation rules.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class DimensionTransformation(str, Enum):
    IDENTITY = "identity"                   # G_full = G_input
    DOUBLE_FLAT_WIDTH = "double_flat_width" # G_full = 2.0 * G_input
    SEAM_OFFSET = "seam_offset"             # G_full = G_input (Linear breadth offset G - B)
    COVERAGE_DELTA = "coverage_delta"       # G_full = G_input (Vertical coverage G - B)


@dataclass(frozen=True)
class DimensionMapping:
    garment_dimension_code: str
    canonical_body_code: str
    transformation: DimensionTransformation
    description: str
    calibration_status: str = "provisional"


class MeasurementCompatibilityRegistry:
    """Canonical registry mapping garment measurements to body measurements."""

    # Explicit mapping table from HFE-001 Section 2.2
    MAPPINGS: Dict[str, DimensionMapping] = {
        "garment_chest_circumference": DimensionMapping(
            garment_dimension_code="garment_chest_circumference",
            canonical_body_code="chest_circumference",
            transformation=DimensionTransformation.IDENTITY,
            description="Horizontal chest girth at nipple apex",
        ),
        "garment_half_chest_width": DimensionMapping(
            garment_dimension_code="garment_half_chest_width",
            canonical_body_code="chest_circumference",
            transformation=DimensionTransformation.DOUBLE_FLAT_WIDTH,
            description="Pit-to-pit flat garment measurement doubled",
        ),
        "garment_waist_circumference": DimensionMapping(
            garment_dimension_code="garment_waist_circumference",
            canonical_body_code="waist_planar_circumference",
            transformation=DimensionTransformation.IDENTITY,
            description="Waistband or waist level inner circumference",
        ),
        "garment_half_waist_width": DimensionMapping(
            garment_dimension_code="garment_half_waist_width",
            canonical_body_code="waist_planar_circumference",
            transformation=DimensionTransformation.DOUBLE_FLAT_WIDTH,
            description="Flat waistband measurement doubled",
        ),
        "garment_hip_circumference": DimensionMapping(
            garment_dimension_code="garment_hip_circumference",
            canonical_body_code="hip_circumference",
            transformation=DimensionTransformation.IDENTITY,
            description="Seat / hip girth at maximal gluteal level",
        ),
        "garment_thigh_circumference": DimensionMapping(
            garment_dimension_code="garment_thigh_circumference",
            canonical_body_code="leg_thigh_circumference",
            transformation=DimensionTransformation.IDENTITY,
            description="Upper leg girth below gluteal fold",
        ),
        "garment_shoulder_seam_width": DimensionMapping(
            garment_dimension_code="garment_shoulder_seam_width",
            canonical_body_code="shoulder_biacromial_breadth",
            transformation=DimensionTransformation.SEAM_OFFSET,
            description="Shoulder seam width acromion-to-acromion across back",
        ),
        "garment_back_length": DimensionMapping(
            garment_dimension_code="garment_back_length",
            canonical_body_code="torso_length",
            transformation=DimensionTransformation.COVERAGE_DELTA,
            description="Garment vertical hem position from C7 vertebra / neck seam",
        ),
    }

    # Deferred dimensions per HFE-001 Section 2.1 & 2.2
    DEFERRED_DIMENSIONS: Dict[str, str] = {
        "garment_neck_circumference": "Tailored shirting collar band girth (requires C7-thyroid notch loop)",
        "garment_inseam_length": "Crotch seam to trouser bottom hem (requires crotch-to-ankle tracking)",
        "garment_sleeve_length": "Acromion to wrist length (Phase 5)",
        "garment_front_rise": "Crotch point to waistband anterior height (Phase 5)",
        "garment_leg_opening": "Pant cuff circumference (Phase 5)",
        "garment_bicep_width": "Upper arm circumference (Phase 5)",
    }

    # Currently available body measurements from AnthropometryEngine
    CURRENTLY_AVAILABLE_BODY_CODES: Set[str] = {
        "stature",
        "shoulder_biacromial_breadth",
        "chest_circumference",
        "waist_planar_circumference",
        "hip_circumference",  # PROVISIONAL
    }

    # Currently unavailable body measurements
    CURRENTLY_UNAVAILABLE_BODY_CODES: Set[str] = {
        "torso_length",
        "leg_thigh_circumference",
        "inseam",
        "sleeve_length",
        "neck_circumference",
    }

    # Category definitions: required core and optional dimensions
    CATEGORY_SPECIFICATIONS: Dict[str, Dict[str, List[str]]] = {
        "t_shirt": {
            "required": [
                "garment_chest_circumference",
                "garment_shoulder_seam_width",
                "garment_back_length",
            ],
            "optional": [
                "garment_half_chest_width",
                "garment_half_waist_width",
                "garment_waist_circumference",
            ],
        },
        "polo": {
            "required": [
                "garment_chest_circumference",
                "garment_shoulder_seam_width",
                "garment_back_length",
            ],
            "optional": [
                "garment_half_chest_width",
                "garment_half_waist_width",
                "garment_waist_circumference",
            ],
        },
        "casual_shirt": {
            "required": [
                "garment_chest_circumference",
                "garment_waist_circumference",
                "garment_shoulder_seam_width",
                "garment_back_length",
            ],
            "optional": [
                "garment_half_chest_width",
                "garment_half_waist_width",
            ],
        },
        "dress_shirt": {
            "required": [
                "garment_chest_circumference",
                "garment_waist_circumference",
                "garment_shoulder_seam_width",
                "garment_back_length",
            ],
            "optional": [
                "garment_half_chest_width",
                "garment_half_waist_width",
            ],
        },
        "trousers": {
            "required": [
                "garment_waist_circumference",
                "garment_hip_circumference",
                "garment_thigh_circumference",
            ],
            "optional": [
                "garment_half_waist_width",
            ],
        },
        "jeans": {
            "required": [
                "garment_waist_circumference",
                "garment_hip_circumference",
                "garment_thigh_circumference",
            ],
            "optional": [
                "garment_half_waist_width",
            ],
        },
    }

    @classmethod
    def get_mapping(cls, garment_dimension_code: str) -> Optional[DimensionMapping]:
        return cls.MAPPINGS.get(garment_dimension_code)

    @classmethod
    def is_deferred(cls, garment_dimension_code: str) -> bool:
        return garment_dimension_code in cls.DEFERRED_DIMENSIONS

    @classmethod
    def is_body_code_available(cls, canonical_body_code: str) -> bool:
        return canonical_body_code in cls.CURRENTLY_AVAILABLE_BODY_CODES

    @classmethod
    def transform_garment_dimension(cls, garment_dimension_code: str, raw_value_cm: float) -> Tuple[str, float]:
        """
        Transforms a garment measurement into its canonical body equivalent code and dimension value.
        e.g., garment_half_chest_width 50.0 cm -> ('chest_circumference', 100.0 cm).
        """
        mapping = cls.get_mapping(garment_dimension_code)
        if not mapping:
            raise KeyError(f"Unknown or unsupported garment dimension code: '{garment_dimension_code}'")

        if mapping.transformation == DimensionTransformation.DOUBLE_FLAT_WIDTH:
            return mapping.canonical_body_code, float(raw_value_cm) * 2.0
        return mapping.canonical_body_code, float(raw_value_cm)

    @classmethod
    def get_required_core_body_dimensions(cls, category: str) -> List[str]:
        """Returns the canonical body measurement codes required for this garment category."""
        spec = cls.CATEGORY_SPECIFICATIONS.get(category.lower())
        if not spec:
            raise ValueError(f"Unsupported garment category: '{category}'")

        body_codes = []
        for g_code in spec["required"]:
            mapping = cls.get_mapping(g_code)
            if mapping and mapping.canonical_body_code not in body_codes:
                body_codes.append(mapping.canonical_body_code)
        return body_codes
