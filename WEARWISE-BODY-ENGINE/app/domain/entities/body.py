"""
WearWise Body Anthropometry and Profile Domain Entities
Pure Python dataclasses enforcing architectural invariants (zero external framework dependencies).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Dict, Optional, Any
from uuid import UUID, uuid4

from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import PresentationGender
from app.domain.exceptions.base import (
    InvalidMeasurementError,
    InvalidControlValueError,
    InvariantViolationError,
)


@dataclass(frozen=True)
class BodyShapeControls:
    """
    Normalized consumer-facing semantic sliders [0.0, 1.0].
    Neutral baseline is 0.50 across all controls.
    """
    shoulder_width: float = 0.50
    chest_fullness: float = 0.50
    belly_fullness: float = 0.50
    waist_definition: float = 0.50
    arm_fullness: float = 0.50
    hip_fullness: float = 0.50
    thigh_fullness: float = 0.50
    calf_fullness: float = 0.50

    def __post_init__(self) -> None:
        control_fields = [
            ("shoulder_width", self.shoulder_width),
            ("chest_fullness", self.chest_fullness),
            ("belly_fullness", self.belly_fullness),
            ("waist_definition", self.waist_definition),
            ("arm_fullness", self.arm_fullness),
            ("hip_fullness", self.hip_fullness),
            ("thigh_fullness", self.thigh_fullness),
            ("calf_fullness", self.calf_fullness),
        ]
        for name, val in control_fields:
            if not isinstance(val, (int, float)):
                raise InvalidControlValueError(
                    f"Control '{name}' must be a float, got {type(val).__name__}",
                    {"control": name, "value": val},
                )
            if math.isnan(val) or math.isinf(val):
                raise InvalidControlValueError(
                    f"Control '{name}' must be finite, got {val}",
                    {"control": name, "value": val},
                )
            if not (0.0 <= float(val) <= 1.0):
                raise InvalidControlValueError(
                    f"Control '{name}' must be between 0.0 and 1.0, got {val}",
                    {"control": name, "value": val},
                )

    def to_dict(self) -> Dict[str, float]:
        return {
            "shoulder_width": self.shoulder_width,
            "chest_fullness": self.chest_fullness,
            "belly_fullness": self.belly_fullness,
            "waist_definition": self.waist_definition,
            "arm_fullness": self.arm_fullness,
            "hip_fullness": self.hip_fullness,
            "thigh_fullness": self.thigh_fullness,
            "calf_fullness": self.calf_fullness,
        }


@dataclass(frozen=True)
class BodyMeasurement:
    """
    A single physical body dimension in centimeters.
    Canonical source of truth for body height (code: 'stature').
    """
    measurement_code: str
    value_cm: Decimal
    unit: str = "cm"
    acquisition_method: MeasurementAcquisitionMethod = MeasurementAcquisitionMethod.USER_REPORTED
    validation_state: MeasurementValidationState = MeasurementValidationState.UNVALIDATED
    lifecycle_status: MeasurementLifecycleStatus = MeasurementLifecycleStatus.ACTIVE
    assessment_state: MeasurementAssessmentState = MeasurementAssessmentState.ELIGIBLE
    landmark_convention: str = "standard_landmark"
    tolerance_cm: Decimal = Decimal("1.00")
    reliability_weight: Decimal = Decimal("1.00")
    measurement_id: UUID = field(default_factory=uuid4)
    profile_id: Optional[UUID] = None
    revision_number: int = 1
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.measurement_code or not isinstance(self.measurement_code, str):
            raise InvalidMeasurementError("Measurement code must be a non-empty string.")

        if self.unit != "cm":
            raise InvalidMeasurementError(f"Measurement unit must be 'cm', got '{self.unit}'.")

        try:
            val = Decimal(str(self.value_cm))
        except Exception:
            raise InvalidMeasurementError(f"Measurement value must be numeric, got {self.value_cm}")

        if val.is_nan() or val.is_infinite() or val <= Decimal("0.0"):
            raise InvalidMeasurementError(
                f"Measurement '{self.measurement_code}' value must be positive finite, got {self.value_cm}"
            )

        try:
            tol = Decimal(str(self.tolerance_cm))
        except Exception:
            raise InvalidMeasurementError(f"Tolerance must be numeric, got {self.tolerance_cm}")

        if tol.is_nan() or tol.is_infinite() or tol < Decimal("0.0"):
            raise InvalidMeasurementError(
                f"Measurement '{self.measurement_code}' tolerance must be non-negative, got {self.tolerance_cm}"
            )

        try:
            rel = Decimal(str(self.reliability_weight))
        except Exception:
            raise InvalidMeasurementError(f"Reliability weight must be numeric, got {self.reliability_weight}")

        if rel.is_nan() or rel.is_infinite() or not (Decimal("0.0") <= rel <= Decimal("1.0")):
            raise InvalidMeasurementError(
                f"Measurement '{self.measurement_code}' reliability_weight must be in [0.0, 1.0], got {self.reliability_weight}"
            )

        if not isinstance(self.acquisition_method, MeasurementAcquisitionMethod):
            raise InvalidMeasurementError(f"Invalid acquisition_method: {self.acquisition_method}")

        if not isinstance(self.validation_state, MeasurementValidationState):
            raise InvalidMeasurementError(f"Invalid validation_state: {self.validation_state}")

        if not isinstance(self.lifecycle_status, MeasurementLifecycleStatus):
            raise InvalidMeasurementError(f"Invalid lifecycle_status: {self.lifecycle_status}")

        if not isinstance(self.assessment_state, MeasurementAssessmentState):
            raise InvalidMeasurementError(f"Invalid assessment_state: {self.assessment_state}")


@dataclass(frozen=True)
class ProfileRevision:
    """
    Immutable revision snapshot for a body profile.
    """
    profile_id: UUID
    revision_number: int
    measurements: Dict[str, BodyMeasurement] = field(default_factory=dict)
    shape_controls: BodyShapeControls = field(default_factory=BodyShapeControls)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revision_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.revision_number < 1:
            raise InvariantViolationError(f"Revision number must be >= 1, got {self.revision_number}")


@dataclass(frozen=True)
class BodyProfile:
    """
    Persistent identity anchor for a shopper.
    """
    user_id: UUID
    presentation_gender: PresentationGender
    stature_cm: Decimal
    reported_weight_kg: Optional[Decimal] = None
    current_revision: int = 1
    profile_id: UUID = field(default_factory=uuid4)
    is_deleted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.presentation_gender, PresentationGender):
            raise InvariantViolationError(
                f"presentation_gender must be a PresentationGender enum, got {self.presentation_gender}"
            )

        try:
            stat = Decimal(str(self.stature_cm))
        except Exception:
            raise InvariantViolationError(f"stature_cm must be numeric, got {self.stature_cm}")

        if stat.is_nan() or stat.is_infinite() or not (Decimal("100.0") <= stat <= Decimal("230.0")):
            raise InvariantViolationError(
                f"stature_cm must be within anatomical range [100.0, 230.0] cm, got {self.stature_cm}"
            )

        if self.reported_weight_kg is not None:
            try:
                wt = Decimal(str(self.reported_weight_kg))
            except Exception:
                raise InvariantViolationError(f"reported_weight_kg must be numeric, got {self.reported_weight_kg}")
            if wt.is_nan() or wt.is_infinite() or not (Decimal("30.0") <= wt <= Decimal("300.0")):
                raise InvariantViolationError(
                    f"reported_weight_kg must be within [30.0, 300.0] kg, got {self.reported_weight_kg}"
                )

        if self.current_revision < 1:
            raise InvariantViolationError(f"current_revision must be >= 1, got {self.current_revision}")
