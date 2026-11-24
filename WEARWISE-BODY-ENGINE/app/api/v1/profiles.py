"""
FastAPI Router for Body Profiles, Revisions, Measurements, and Semantic Controls
Endpoint base: /api/v1
"""

import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_user_id
from app.services.profile_service import ProfileService
from app.repositories.avatar_repository import AvatarRepository
from app.domain.entities.body import CONTROL_SAFE_RANGES
from app.api.schemas.profiles import (
    CreateProfileRequest,
    UpdateProfileRequest,
    RecordMeasurementsRequest,
    UpdateControlsRequest,
    ProfileResponse,
)

router = APIRouter(tags=["Profiles & Measurements"])


@router.get("/profiles", response_model=List[ProfileResponse])
def list_profiles(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Lists all body profiles owned by the authenticated user."""
    srv = ProfileService(db)
    avatar_repo = AvatarRepository(db)
    profiles = srv.list_profiles(user_id)
    results = []
    for p in profiles:
        latest_rev = srv.repo.get_latest_revision(p.id)
        active_m = {
            m.measurement_code: {
                "value_cm": float(m.value_cm),
                "acquisition_method": m.acquisition_method,
                "validation_state": m.validation_state,
                "lifecycle_status": m.lifecycle_status,
                "assessment_state": m.assessment_state,
                "tolerance_cm": float(m.tolerance_cm),
            }
            for m in (latest_rev.measurements if latest_rev else [])
            if m.lifecycle_status == "active"
        }
        controls = {}
        if latest_rev and latest_rev.shape_controls:
            sc = latest_rev.shape_controls
            controls = {
                "shoulder_width": float(sc.shoulder_width),
                "chest_fullness": float(sc.chest_fullness),
                "belly_fullness": float(sc.belly_fullness),
                "waist_definition": float(sc.waist_definition),
                "arm_fullness": float(sc.arm_fullness),
                "hip_fullness": float(sc.hip_fullness),
                "thigh_fullness": float(sc.thigh_fullness),
                "calf_fullness": float(sc.calf_fullness),
            }
        latest_asset = avatar_repo.get_latest_avatar_asset_for_profile(p.id)
        asset_url = f"/api/v1/avatar/assets/{latest_asset.id}.glb" if latest_asset else None
        results.append(
            ProfileResponse(
                profile_id=str(p.id),
                user_id=str(p.user_id),
                current_revision=p.current_revision,
                presentation_gender=p.presentation_gender,
                stature_cm=float(p.stature_cm),
                reported_weight_kg=float(p.reported_weight_kg) if p.reported_weight_kg is not None else None,
                active_measurements=active_m,
                shape_controls=controls,
                latest_asset_url=asset_url,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
        )
    return results


@router.post("/profiles", status_code=status.HTTP_201_CREATED, response_model=ProfileResponse)
def create_profile(
    payload: CreateProfileRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Creates a new body profile anchor for the authenticated user,
    initializing revision 1, canonical stature, and shape controls.
    """
    srv = ProfileService(db)
    profile = srv.create_profile(
        requesting_user_id=user_id,
        presentation_gender=payload.presentation_gender,
        stature_cm=payload.stature_cm,
        reported_weight_kg=payload.reported_weight_kg,
        initial_controls=payload.initial_controls,
    )
    db.commit()

    # Format response
    latest_rev = srv.repo.get_latest_revision(profile.id)
    active_m = {
        m.measurement_code: {
            "value_cm": float(m.value_cm),
            "acquisition_method": m.acquisition_method,
            "validation_state": m.validation_state,
            "lifecycle_status": m.lifecycle_status,
            "assessment_state": m.assessment_state,
            "tolerance_cm": float(m.tolerance_cm),
        }
        for m in latest_rev.measurements
        if m.lifecycle_status == "active"
    }
    controls = {}
    if latest_rev.shape_controls:
        sc = latest_rev.shape_controls
        controls = {
            "shoulder_width": float(sc.shoulder_width),
            "chest_fullness": float(sc.chest_fullness),
            "belly_fullness": float(sc.belly_fullness),
            "waist_definition": float(sc.waist_definition),
            "arm_fullness": float(sc.arm_fullness),
            "hip_fullness": float(sc.hip_fullness),
            "thigh_fullness": float(sc.thigh_fullness),
            "calf_fullness": float(sc.calf_fullness),
        }

    return ProfileResponse(
        profile_id=str(profile.id),
        user_id=str(profile.user_id),
        current_revision=profile.current_revision,
        presentation_gender=profile.presentation_gender,
        stature_cm=float(profile.stature_cm),
        reported_weight_kg=float(profile.reported_weight_kg) if profile.reported_weight_kg is not None else None,
        active_measurements=active_m,
        shape_controls=controls,
        latest_asset_url=None,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves profile summary and active measurements for authenticated owner."""
    srv = ProfileService(db)
    profile = srv.get_profile(profile_id, user_id)
    latest_rev = srv.repo.get_latest_revision(profile.id)

    active_m = {
        m.measurement_code: {
            "value_cm": float(m.value_cm),
            "acquisition_method": m.acquisition_method,
            "validation_state": m.validation_state,
            "lifecycle_status": m.lifecycle_status,
            "assessment_state": m.assessment_state,
            "tolerance_cm": float(m.tolerance_cm),
        }
        for m in (latest_rev.measurements if latest_rev else [])
        if m.lifecycle_status == "active"
    }
    controls = {}
    if latest_rev and latest_rev.shape_controls:
        sc = latest_rev.shape_controls
        controls = {
            "shoulder_width": float(sc.shoulder_width),
            "chest_fullness": float(sc.chest_fullness),
            "belly_fullness": float(sc.belly_fullness),
            "waist_definition": float(sc.waist_definition),
            "arm_fullness": float(sc.arm_fullness),
            "hip_fullness": float(sc.hip_fullness),
            "thigh_fullness": float(sc.thigh_fullness),
            "calf_fullness": float(sc.calf_fullness),
        }

    # Latest asset URL if generated
    avatar_repo = AvatarRepository(db)
    latest_asset = avatar_repo.get_latest_avatar_asset_for_profile(profile_id)
    asset_url = f"/api/v1/avatar/assets/{latest_asset.id}.glb" if latest_asset else None

    return ProfileResponse(
        profile_id=str(profile.id),
        user_id=str(profile.user_id),
        current_revision=profile.current_revision,
        presentation_gender=profile.presentation_gender,
        stature_cm=float(profile.stature_cm),
        reported_weight_kg=float(profile.reported_weight_kg) if profile.reported_weight_kg is not None else None,
        active_measurements=active_m,
        shape_controls=controls,
        latest_asset_url=asset_url,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.patch("/profiles/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: uuid.UUID,
    payload: UpdateProfileRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Updates non-anthropometric profile metadata."""
    srv = ProfileService(db)
    profile = srv.update_profile_metadata(
        profile_id=profile_id,
        requesting_user_id=user_id,
        presentation_gender=payload.presentation_gender,
        reported_weight_kg=payload.reported_weight_kg,
    )
    db.commit()
    return get_profile(profile_id=profile_id, user_id=user_id, db=db)


@router.get("/profiles/{profile_id}/revisions")
def get_revisions(
    profile_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Returns revision history for profile."""
    srv = ProfileService(db)
    revs = srv.get_revisions(profile_id, user_id)
    return {
        "profile_id": str(profile_id),
        "revisions": [
            {
                "revision_number": r.revision_number,
                "created_at": r.created_at.isoformat(),
                "measurement_count": len(r.measurements),
                "has_controls": r.shape_controls is not None,
            }
            for r in revs
        ],
    }


@router.post("/profiles/{profile_id}/measurements")
def record_measurements(
    profile_id: uuid.UUID,
    payload: RecordMeasurementsRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Appends a new revision with recorded measurements.
    Enforces optimistic locking on expected_revision.
    """
    srv = ProfileService(db)
    meas_dicts = [m.model_dump() for m in payload.measurements]
    result = srv.record_measurements(
        profile_id=profile_id,
        requesting_user_id=user_id,
        expected_revision=payload.expected_revision,
        measurements=meas_dicts,
    )
    db.commit()
    return result


@router.get("/profiles/{profile_id}/measurements")
def get_measurements(
    profile_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves active measurements for the profile."""
    srv = ProfileService(db)
    profile = srv.get_profile(profile_id, user_id)
    latest_rev = srv.repo.get_latest_revision(profile.id)
    active = {
        m.measurement_code: {
            "value_cm": float(m.value_cm),
            "unit": m.unit,
            "acquisition_method": m.acquisition_method,
            "validation_state": m.validation_state,
            "lifecycle_status": m.lifecycle_status,
            "assessment_state": m.assessment_state,
            "tolerance_cm": float(m.tolerance_cm),
            "reliability_weight": float(m.reliability_weight),
            "landmark_convention": m.landmark_convention,
        }
        for m in (latest_rev.measurements if latest_rev else [])
        if m.lifecycle_status == "active"
    }
    return {
        "profile_id": str(profile_id),
        "current_revision": profile.current_revision,
        "measurements": active,
    }


@router.get("/profiles/{profile_id}/measurements/history")
def get_measurement_history(
    profile_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves timeline of measurements across revisions."""
    srv = ProfileService(db)
    revs = srv.get_revisions(profile_id, user_id)
    history = []
    for r in revs:
        for m in r.measurements:
            history.append({
                "revision_number": r.revision_number,
                "measurement_code": m.measurement_code,
                "value_cm": float(m.value_cm),
                "acquisition_method": m.acquisition_method,
                "validation_state": m.validation_state,
                "captured_at": m.captured_at.isoformat(),
            })
    return {"profile_id": str(profile_id), "history": history}


@router.get("/controls/definitions")
def get_control_definitions():
    """Returns supported semantic controls catalog and safe bounds."""
    definitions = {}
    for ctrl, (min_v, max_v) in CONTROL_SAFE_RANGES.items():
        definitions[ctrl] = {
            "name": ctrl,
            "display_name": ctrl.replace("_", " ").title(),
            "default_value": 0.50,
            "safe_min": min_v,
            "safe_max": max_v,
        }
    return {"controls": definitions}


@router.put("/profiles/{profile_id}/controls")
def update_controls(
    profile_id: uuid.UUID,
    payload: UpdateControlsRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Updates semantic body controls by creating a new revision.
    """
    srv = ProfileService(db)
    result = srv.update_controls(
        profile_id=profile_id,
        requesting_user_id=user_id,
        expected_revision=payload.expected_revision,
        controls=payload.controls,
    )
    db.commit()
    return result
