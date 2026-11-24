"""
WearWise Profile Repository
Handles transactional persistence and queries for body profiles, revisions, measurements, and controls.
Enforces canonical stature initialization, optimistic locking, and revision immutability.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    BodyProfileModel,
    ProfileRevisionModel,
    BodyMeasurementModel,
    BodyShapeControlsModel,
)


class ConcurrencyError(Exception):
    """Raised when expected_revision does not match current_revision."""
    pass


class ProfileRepository:
    """Repository for BodyProfile and associated revision aggregate."""

    def __init__(self, db: Session):
        self.db = db

    def create_profile(
        self,
        user_id: uuid.UUID,
        presentation_gender: str,
        stature_cm: Decimal,
        reported_weight_kg: Optional[Decimal] = None,
        initial_controls: Optional[Dict[str, float]] = None,
    ) -> BodyProfileModel:
        """
        Atomically creates a new body profile with initial revision 1,
        canonical stature measurement, and initial shape controls.
        """
        profile = BodyProfileModel(
            user_id=user_id,
            current_revision=1,
            presentation_gender=presentation_gender,
            stature_cm=stature_cm,
            reported_weight_kg=reported_weight_kg,
            is_deleted=False,
        )
        self.db.add(profile)
        self.db.flush()

        # Initial revision
        rev = ProfileRevisionModel(
            profile_id=profile.id,
            revision_number=1,
        )
        self.db.add(rev)
        self.db.flush()

        # Canonical Stature Measurement
        stature_meas = BodyMeasurementModel(
            revision_id=rev.id,
            measurement_code="stature",
            value_cm=stature_cm,
            unit="cm",
            acquisition_method="user_reported",
            validation_state="unvalidated",
            lifecycle_status="active",
            assessment_state="eligible",
            landmark_convention="plantar_to_vertex_bounding_box",
            tolerance_cm=Decimal("1.00"),
            reliability_weight=Decimal("1.00"),
        )
        self.db.add(stature_meas)

        # Initial Shape Controls
        ctrls = initial_controls or {}
        shape_ctrl = BodyShapeControlsModel(
            revision_id=rev.id,
            shoulder_width=Decimal(str(ctrls.get("shoulder_width", 0.50))),
            chest_fullness=Decimal(str(ctrls.get("chest_fullness", 0.50))),
            belly_fullness=Decimal(str(ctrls.get("belly_fullness", 0.50))),
            waist_definition=Decimal(str(ctrls.get("waist_definition", 0.50))),
            arm_fullness=Decimal(str(ctrls.get("arm_fullness", 0.50))),
            hip_fullness=Decimal(str(ctrls.get("hip_fullness", 0.50))),
            thigh_fullness=Decimal(str(ctrls.get("thigh_fullness", 0.50))),
            calf_fullness=Decimal(str(ctrls.get("calf_fullness", 0.50))),
        )
        self.db.add(shape_ctrl)
        self.db.flush()

        return profile

    def get_profile(self, profile_id: uuid.UUID) -> Optional[BodyProfileModel]:
        """Retrieves profile with active revisions loaded."""
        stmt = (
            select(BodyProfileModel)
            .where(and_(BodyProfileModel.id == profile_id, BodyProfileModel.is_deleted == False))  # noqa: E712
            .options(
                joinedload(BodyProfileModel.revisions)
                .joinedload(ProfileRevisionModel.measurements),
                joinedload(BodyProfileModel.revisions)
                .joinedload(ProfileRevisionModel.shape_controls),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_profiles_by_user(self, user_id: uuid.UUID) -> List[BodyProfileModel]:
        """Retrieves all active profiles for a given user."""
        stmt = (
            select(BodyProfileModel)
            .where(and_(BodyProfileModel.user_id == user_id, BodyProfileModel.is_deleted == False))  # noqa: E712
            .options(
                joinedload(BodyProfileModel.revisions)
                .joinedload(ProfileRevisionModel.measurements),
                joinedload(BodyProfileModel.revisions)
                .joinedload(ProfileRevisionModel.shape_controls),
            )
            .order_by(BodyProfileModel.created_at.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def update_profile_metadata(
        self,
        profile_id: uuid.UUID,
        presentation_gender: Optional[str] = None,
        reported_weight_kg: Optional[Decimal] = None,
    ) -> Optional[BodyProfileModel]:
        """Updates non-anthropometric profile metadata."""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        if presentation_gender is not None:
            profile.presentation_gender = presentation_gender
        if reported_weight_kg is not None:
            profile.reported_weight_kg = reported_weight_kg
        self.db.flush()
        return profile

    def get_latest_revision(self, profile_id: uuid.UUID) -> Optional[ProfileRevisionModel]:
        """Returns the current active revision with measurements and shape controls."""
        stmt = (
            select(ProfileRevisionModel)
            .join(BodyProfileModel, BodyProfileModel.id == ProfileRevisionModel.profile_id)
            .where(
                and_(
                    ProfileRevisionModel.profile_id == profile_id,
                    ProfileRevisionModel.revision_number == BodyProfileModel.current_revision,
                )
            )
            .options(
                joinedload(ProfileRevisionModel.measurements),
                joinedload(ProfileRevisionModel.shape_controls),
                joinedload(ProfileRevisionModel.avatar_configurations),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_revisions(self, profile_id: uuid.UUID) -> List[ProfileRevisionModel]:
        """Returns revision history ordered ascending."""
        stmt = (
            select(ProfileRevisionModel)
            .where(ProfileRevisionModel.profile_id == profile_id)
            .order_by(ProfileRevisionModel.revision_number.asc())
            .options(
                joinedload(ProfileRevisionModel.measurements),
                joinedload(ProfileRevisionModel.shape_controls),
            )
        )
        return list(self.db.scalars(stmt).unique().all())

    def record_measurements(
        self,
        profile_id: uuid.UUID,
        expected_revision: int,
        measurements: List[Dict[str, Any]],
    ) -> Tuple[ProfileRevisionModel, int]:
        """
        Records new measurements by appending an immutable profile revision.
        Enforces optimistic locking against expected_revision.
        Inherits prior active measurements and updates denormalized stature if provided.
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found.")

        if profile.current_revision != expected_revision:
            raise ConcurrencyError(
                f"Optimistic lock conflict: expected revision {expected_revision}, current revision is {profile.current_revision}"
            )

        latest_rev = self.get_latest_revision(profile_id)
        new_rev_number = profile.current_revision + 1
        profile.current_revision = new_rev_number

        new_rev = ProfileRevisionModel(
            profile_id=profile_id,
            revision_number=new_rev_number,
        )
        self.db.add(new_rev)
        self.db.flush()

        # Copy existing shape controls to new revision
        if latest_rev and latest_rev.shape_controls:
            ctrls = latest_rev.shape_controls
            new_ctrl = BodyShapeControlsModel(
                revision_id=new_rev.id,
                shoulder_width=ctrls.shoulder_width,
                chest_fullness=ctrls.chest_fullness,
                belly_fullness=ctrls.belly_fullness,
                waist_definition=ctrls.waist_definition,
                arm_fullness=ctrls.arm_fullness,
                hip_fullness=ctrls.hip_fullness,
                thigh_fullness=ctrls.thigh_fullness,
                calf_fullness=ctrls.calf_fullness,
            )
            self.db.add(new_ctrl)

        # Build existing measurement map from latest revision
        active_map: Dict[str, BodyMeasurementModel] = {}
        if latest_rev:
            for m in latest_rev.measurements:
                if m.lifecycle_status == "active":
                    active_map[m.measurement_code] = m

        # Process incoming measurements
        for m_in in measurements:
            code = m_in["measurement_code"]
            val_cm = Decimal(str(m_in["value_cm"]))
            if code == "stature":
                profile.stature_cm = val_cm

            # Mark previously active measurement with same code as superseded if updating
            m_obj = BodyMeasurementModel(
                revision_id=new_rev.id,
                measurement_code=code,
                value_cm=val_cm,
                unit=m_in.get("unit", "cm"),
                acquisition_method=m_in.get("acquisition_method", "tape_measured"),
                validation_state=m_in.get("validation_state", "internally_consistent"),
                lifecycle_status="active",
                assessment_state=m_in.get("assessment_state", "eligible"),
                landmark_convention=m_in.get("landmark_convention", "standard_landmark"),
                tolerance_cm=Decimal(str(m_in.get("tolerance_cm", 1.00))),
                reliability_weight=Decimal(str(m_in.get("reliability_weight", 1.00))),
            )
            active_map[code] = m_obj

        # Add all active measurements to new revision
        for m_model in active_map.values():
            if m_model.revision_id != new_rev.id:
                # Clone inherited measurement into new revision
                cloned = BodyMeasurementModel(
                    revision_id=new_rev.id,
                    measurement_code=m_model.measurement_code,
                    value_cm=m_model.value_cm,
                    unit=m_model.unit,
                    acquisition_method=m_model.acquisition_method,
                    validation_state=m_model.validation_state,
                    lifecycle_status="active",
                    assessment_state=m_model.assessment_state,
                    landmark_convention=m_model.landmark_convention,
                    tolerance_cm=m_model.tolerance_cm,
                    reliability_weight=m_model.reliability_weight,
                )
                self.db.add(cloned)
            else:
                self.db.add(m_model)

        self.db.flush()
        return new_rev, len(measurements)

    def update_controls(
        self,
        profile_id: uuid.UUID,
        expected_revision: int,
        controls: Dict[str, float],
    ) -> ProfileRevisionModel:
        """
        Updates semantic controls by appending a new revision.
        Inherits prior active measurements.
        """
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found.")

        if profile.current_revision != expected_revision:
            raise ConcurrencyError(
                f"Optimistic lock conflict: expected revision {expected_revision}, current revision is {profile.current_revision}"
            )

        latest_rev = self.get_latest_revision(profile_id)
        new_rev_number = profile.current_revision + 1
        profile.current_revision = new_rev_number

        new_rev = ProfileRevisionModel(
            profile_id=profile_id,
            revision_number=new_rev_number,
        )
        self.db.add(new_rev)
        self.db.flush()

        # Merge previous controls with updates
        old_ctrls = latest_rev.shape_controls if latest_rev and latest_rev.shape_controls else None
        new_ctrl = BodyShapeControlsModel(
            revision_id=new_rev.id,
            shoulder_width=Decimal(str(controls.get("shoulder_width", float(old_ctrls.shoulder_width) if old_ctrls else 0.50))),
            chest_fullness=Decimal(str(controls.get("chest_fullness", float(old_ctrls.chest_fullness) if old_ctrls else 0.50))),
            belly_fullness=Decimal(str(controls.get("belly_fullness", float(old_ctrls.belly_fullness) if old_ctrls else 0.50))),
            waist_definition=Decimal(str(controls.get("waist_definition", float(old_ctrls.waist_definition) if old_ctrls else 0.50))),
            arm_fullness=Decimal(str(controls.get("arm_fullness", float(old_ctrls.arm_fullness) if old_ctrls else 0.50))),
            hip_fullness=Decimal(str(controls.get("hip_fullness", float(old_ctrls.hip_fullness) if old_ctrls else 0.50))),
            thigh_fullness=Decimal(str(controls.get("thigh_fullness", float(old_ctrls.thigh_fullness) if old_ctrls else 0.50))),
            calf_fullness=Decimal(str(controls.get("calf_fullness", float(old_ctrls.calf_fullness) if old_ctrls else 0.50))),
        )
        self.db.add(new_ctrl)

        # Inherit active measurements
        if latest_rev:
            for m in latest_rev.measurements:
                if m.lifecycle_status == "active":
                    cloned = BodyMeasurementModel(
                        revision_id=new_rev.id,
                        measurement_code=m.measurement_code,
                        value_cm=m.value_cm,
                        unit=m.unit,
                        acquisition_method=m.acquisition_method,
                        validation_state=m.validation_state,
                        lifecycle_status="active",
                        assessment_state=m.assessment_state,
                        landmark_convention=m.landmark_convention,
                        tolerance_cm=m.tolerance_cm,
                        reliability_weight=m.reliability_weight,
                    )
                    self.db.add(cloned)

        self.db.flush()
        return new_rev
