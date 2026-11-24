"""
WearWise Profile Application Service
Orchestrates profile creation, revisions, measurements, and semantic control updates.
Strictly verifies that the requesting user owns the target profile.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.repositories.profile_repository import ProfileRepository, ConcurrencyError
from app.db.models import BodyProfileModel, ProfileRevisionModel, BodyMeasurementModel
from app.services.errors import NotFoundError, ForbiddenError, ConflictError, ValidationError


class ProfileService:
    """Application service for shopper profile operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)

    def _verify_profile_owner(self, profile: BodyProfileModel, requesting_user_id: uuid.UUID) -> None:
        """Verifies that requesting user owns the profile."""
        if profile.user_id != requesting_user_id:
            raise ForbiddenError(
                "Access denied: You do not have permission to access or modify this profile.",
                code="OWNERSHIP_VIOLATION",
            )

    def create_profile(
        self,
        requesting_user_id: uuid.UUID,
        presentation_gender: str,
        stature_cm: float,
        reported_weight_kg: Optional[float] = None,
        initial_controls: Optional[Dict[str, float]] = None,
    ) -> BodyProfileModel:
        """
        Creates a new profile for the authenticated user with initial revision,
        canonical stature measurement, and shape controls.
        """
        if presentation_gender not in ("masculine", "feminine", "neutral"):
            raise ValidationError(
                f"Invalid presentation_gender '{presentation_gender}'. Must be 'masculine', 'feminine', or 'neutral'.",
                code="INVALID_GENDER",
            )

        if not (100.0 <= stature_cm <= 230.0):
            raise ValidationError(
                f"Stature ({stature_cm} cm) is outside safe anatomical bounds [100.0, 230.0] cm.",
                code="MEASUREMENT_OUT_OF_BOUNDS",
            )

        if reported_weight_kg is not None and not (30.0 <= reported_weight_kg <= 300.0):
            raise ValidationError(
                f"Reported weight ({reported_weight_kg} kg) is outside permitted bounds [30.0, 300.0] kg.",
                code="WEIGHT_OUT_OF_BOUNDS",
            )

        stat_dec = Decimal(f"{stature_cm:.2f}")
        wt_dec = Decimal(f"{reported_weight_kg:.2f}") if reported_weight_kg is not None else None

        profile = self.repo.create_profile(
            user_id=requesting_user_id,
            presentation_gender=presentation_gender,
            stature_cm=stat_dec,
            reported_weight_kg=wt_dec,
            initial_controls=initial_controls,
        )
        return profile

    def get_profile(self, profile_id: uuid.UUID, requesting_user_id: uuid.UUID) -> BodyProfileModel:
        """Retrieves profile if owned by requesting user."""
        profile = self.repo.get_profile(profile_id)
        if not profile:
            raise NotFoundError(f"Profile {profile_id} was not found.")
        self._verify_profile_owner(profile, requesting_user_id)
        return profile

    def list_profiles(self, requesting_user_id: uuid.UUID) -> List[BodyProfileModel]:
        """Lists all profiles owned by requesting user."""
        return self.repo.get_profiles_by_user(requesting_user_id)

    def update_profile_metadata(
        self,
        profile_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        presentation_gender: Optional[str] = None,
        reported_weight_kg: Optional[float] = None,
    ) -> BodyProfileModel:
        """Updates non-anthropometric metadata after verifying ownership."""
        profile = self.get_profile(profile_id, requesting_user_id)
        if presentation_gender is not None and presentation_gender not in ("masculine", "feminine", "neutral"):
            raise ValidationError(f"Invalid presentation_gender '{presentation_gender}'")
        
        wt_dec = Decimal(f"{reported_weight_kg:.2f}") if reported_weight_kg is not None else None
        updated = self.repo.update_profile_metadata(
            profile_id=profile_id,
            presentation_gender=presentation_gender,
            reported_weight_kg=wt_dec,
        )
        return updated or profile

    def get_revisions(self, profile_id: uuid.UUID, requesting_user_id: uuid.UUID) -> List[ProfileRevisionModel]:
        """Retrieves revision history for a profile."""
        self.get_profile(profile_id, requesting_user_id)
        return self.repo.get_revisions(profile_id)

    def record_measurements(
        self,
        profile_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        expected_revision: int,
        measurements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Appends a new revision with recorded measurements.
        Enforces optimistic locking and profile ownership.
        """
        self.get_profile(profile_id, requesting_user_id)
        try:
            new_rev, recorded_count = self.repo.record_measurements(
                profile_id=profile_id,
                expected_revision=expected_revision,
                measurements=measurements,
            )
        except ConcurrencyError as e:
            raise ConflictError(str(e))

        active_measurements = {
            m.measurement_code: {
                "value_cm": float(m.value_cm),
                "acquisition_method": m.acquisition_method,
                "validation_state": m.validation_state,
                "lifecycle_status": m.lifecycle_status,
                "assessment_state": m.assessment_state,
                "tolerance_cm": float(m.tolerance_cm),
            }
            for m in new_rev.measurements
            if m.lifecycle_status == "active"
        }

        return {
            "profile_id": str(profile_id),
            "new_revision": new_rev.revision_number,
            "recorded_count": recorded_count,
            "active_measurements": active_measurements,
        }

    def update_controls(
        self,
        profile_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
        expected_revision: int,
        controls: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Updates semantic body controls by appending a new revision.
        Enforces safe range limits and optimistic locking.
        """
        self.get_profile(profile_id, requesting_user_id)
        for ctrl, val in controls.items():
            if not (0.0 <= val <= 1.0):
                raise ValidationError(f"Control '{ctrl}' must be in [0.0, 1.0], got {val}")

        try:
            new_rev = self.repo.update_controls(
                profile_id=profile_id,
                expected_revision=expected_revision,
                controls=controls,
            )
        except ConcurrencyError as e:
            raise ConflictError(str(e))

        ctrl_dict = {}
        if new_rev.shape_controls:
            ctrl_dict = {
                "shoulder_width": float(new_rev.shape_controls.shoulder_width),
                "chest_fullness": float(new_rev.shape_controls.chest_fullness),
                "belly_fullness": float(new_rev.shape_controls.belly_fullness),
                "waist_definition": float(new_rev.shape_controls.waist_definition),
                "arm_fullness": float(new_rev.shape_controls.arm_fullness),
                "hip_fullness": float(new_rev.shape_controls.hip_fullness),
                "thigh_fullness": float(new_rev.shape_controls.thigh_fullness),
                "calf_fullness": float(new_rev.shape_controls.calf_fullness),
            }

        return {
            "profile_id": str(profile_id),
            "new_revision": new_rev.revision_number,
            "controls": ctrl_dict,
            "is_avatar_stale": True,
        }
