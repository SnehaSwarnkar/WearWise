"""
WearWise Garment and Fit Domain Entities
Pure Python dataclasses for garments, sizes, measurements, and fit recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Dict, Optional, Any, List
from uuid import UUID, uuid4

from app.domain.taxonomies.garment import FabricStretchDirection, RegionalFitClassification
from app.domain.exceptions.base import InvariantViolationError


@dataclass(frozen=True)
class FabricProperties:
    """Mechanical and structural fabric specifications."""
    fibre_composition: Dict[str, float]
    mechanical_stretch_pct: float     # Measured extension under standard load (e.g. 0.045 for 4.5%)
    stretch_recovery_pct: float       # Elastic recovery ratio (e.g. 0.92 for 92%)
    stretch_direction: FabricStretchDirection

    def __post_init__(self) -> None:
        if not isinstance(self.stretch_direction, FabricStretchDirection):
            raise InvariantViolationError(f"stretch_direction must be FabricStretchDirection, got {self.stretch_direction}")

        if not isinstance(self.mechanical_stretch_pct, (int, float)) or not math.isfinite(self.mechanical_stretch_pct):
            raise InvariantViolationError("mechanical_stretch_pct must be finite.")
        if self.mechanical_stretch_pct < 0.0:
            raise InvariantViolationError("mechanical_stretch_pct cannot be negative.")

        if not isinstance(self.stretch_recovery_pct, (int, float)) or not math.isfinite(self.stretch_recovery_pct):
            raise InvariantViolationError("stretch_recovery_pct must be finite.")
        if not (0.0 <= self.stretch_recovery_pct <= 1.0):
            raise InvariantViolationError("stretch_recovery_pct must be in [0.0, 1.0].")

        # Invariant: rigid_zero requires stretch < 2%
        if self.stretch_direction == FabricStretchDirection.RIGID_ZERO and self.mechanical_stretch_pct >= 0.02:
            raise InvariantViolationError(
                f"stretch_direction 'rigid_zero' requires mechanical_stretch_pct < 0.02, got {self.mechanical_stretch_pct}"
            )


@dataclass(frozen=True)
class GarmentMeasurement:
    """A finished garment dimension for a specific size."""
    dimension_code: str
    value_cm: Decimal
    tolerance_cm: Decimal = Decimal("1.00")
    measurement_procedure: str = "straight_across_relaxed"
    provenance: str = "brand_size_chart"
    measurement_id: UUID = field(default_factory=uuid4)
    size_id: Optional[UUID] = None

    def __post_init__(self) -> None:
        if not self.dimension_code:
            raise InvariantViolationError("dimension_code must be a non-empty string.")
        val = Decimal(str(self.value_cm))
        if val.is_nan() or val.is_infinite() or val <= Decimal("0.0"):
            raise InvariantViolationError(f"Garment measurement value must be positive finite, got {self.value_cm}")
        tol = Decimal(str(self.tolerance_cm))
        if tol.is_nan() or tol.is_infinite() or tol < Decimal("0.0"):
            raise InvariantViolationError(f"Garment measurement tolerance must be non-negative, got {self.tolerance_cm}")


@dataclass(frozen=True)
class GarmentSize:
    """Size variant for a garment revision (e.g. 'M', 'L')."""
    size_label: str
    sort_order: int = 0
    measurements: Dict[str, GarmentMeasurement] = field(default_factory=dict)
    size_id: UUID = field(default_factory=uuid4)
    garment_revision_id: Optional[UUID] = None

    def __post_init__(self) -> None:
        if not self.size_label:
            raise InvariantViolationError("size_label must be a non-empty string.")


@dataclass(frozen=True)
class GarmentRevision:
    """Immutable specification revision of a garment."""
    revision_number: int
    fabric_properties: FabricProperties
    sizes: Dict[str, GarmentSize] = field(default_factory=dict)
    revision_id: UUID = field(default_factory=uuid4)
    garment_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.revision_number < 1:
            raise InvariantViolationError(f"revision_number must be >= 1, got {self.revision_number}")


@dataclass(frozen=True)
class GarmentProfile:
    """Garment master record owned by an authenticated merchant brand."""
    brand_id: UUID
    sku: str
    title: str
    category: str
    current_revision: int = 1
    garment_id: UUID = field(default_factory=uuid4)
    is_deleted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.sku:
            raise InvariantViolationError("sku must be a non-empty string.")
        if not self.title:
            raise InvariantViolationError("title must be a non-empty string.")
        if not self.category:
            raise InvariantViolationError("category must be a non-empty string.")
        if self.current_revision < 1:
            raise InvariantViolationError("current_revision must be >= 1.")


@dataclass(frozen=True)
class RegionalFitEvaluation:
    """Detailed regional ease comparison for an individual body zone."""
    region_code: str
    body_measurement_cm: float
    garment_dimension_cm: float
    ease_cm: float
    classification: RegionalFitClassification
    explanation: str


@dataclass(frozen=True)
class FitRecommendation:
    """Personalized sizing recommendation result."""
    profile_revision_id: UUID
    garment_revision_id: UUID
    recommended_size: str
    composite_score: float             # Bounded score [0.0, 100.0]
    coverage_ratio: float              # Evaluated evidence coverage ratio
    regional_evaluations: List[RegionalFitEvaluation] = field(default_factory=list)
    rulebook_version: str = "1.2.1"
    recommendation_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.recommended_size:
            raise InvariantViolationError("recommended_size must be a non-empty string.")
        if not (0.0 <= self.composite_score <= 100.0) or not math.isfinite(self.composite_score):
            raise InvariantViolationError(f"composite_score must be in [0.0, 100.0], got {self.composite_score}")
        if self.coverage_ratio < 0.0 or not math.isfinite(self.coverage_ratio):
            raise InvariantViolationError(f"coverage_ratio must be non-negative finite, got {self.coverage_ratio}")
