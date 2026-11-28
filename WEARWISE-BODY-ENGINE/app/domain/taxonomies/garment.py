"""
WearWise Garment and Presentation Taxonomies
"""

from enum import Enum


class PresentationGender(str, Enum):
    """Visual presentation style for avatar mesh rendering (strictly decoupled from gender identity)."""
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTRAL = "neutral"


class FabricStretchDirection(str, Enum):
    """Directionality of mechanical fabric elasticity."""
    RIGID_ZERO = "rigid_zero"
    MONO_WEFT = "mono_weft"
    MONO_WARP = "mono_warp"
    BI_DIRECTIONAL_FOUR_WAY = "bi_directional_four_way"


class RegionalFitClassification(str, Enum):
    """Non-overlapping 6-tier fit spectrum classification."""
    TOO_TIGHT = "too_tight"       # Ease < Lower_fitted (Constricting / unwearable)
    FITTED = "fitted"             # [Lower_fitted, Upper_fitted) (Tailored silhouette)
    REGULAR = "regular"           # [Lower_regular, Upper_regular) (Standard daily comfort)
    RELAXED = "relaxed"           # [Lower_relaxed, Upper_relaxed) (Casual loose silhouette)
    OVERSIZED = "oversized"       # [Lower_oversized, Upper_oversized) (Streetwear / drop-shoulder)
    TOO_LARGE = "too_large"       # Ease >= Upper_oversized (Excessive volume / poor fit)
