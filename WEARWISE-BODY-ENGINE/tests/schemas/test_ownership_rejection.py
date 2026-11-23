"""
Test Suite: Rejection of Forbidden Client Ownership Fields
Verifies that client request schemas reject client-supplied user_id or brand_id.
"""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.schemas.profile import ProfileCreateRequest, ProfileUpdateRequest
from app.schemas.avatar import AvatarGenerateRequest
from app.schemas.garment import GarmentCreateRequest
from app.schemas.fit import FitRecommendRequest
from app.schemas.measurement import MeasurementRecordRequest, MeasurementItem


def test_profile_create_rejects_user_id():
    """Verify ProfileCreateRequest strictly rejects client-supplied user_id."""
    with pytest.raises(ValidationError) as exc_info:
        ProfileCreateRequest(
            presentation_gender="masculine",
            stature_cm=178.0,
            user_id=str(uuid4()), # type: ignore
        )
    assert "Extra inputs are not permitted" in str(exc_info.value) or "user_id" in str(exc_info.value)


def test_avatar_generate_rejects_user_id():
    """Verify AvatarGenerateRequest strictly rejects client-supplied user_id."""
    with pytest.raises(ValidationError) as exc_info:
        AvatarGenerateRequest(
            profile_id=uuid4(),
            user_id=str(uuid4()), # type: ignore
        )
    assert "Extra inputs are not permitted" in str(exc_info.value) or "user_id" in str(exc_info.value)


def test_garment_create_rejects_brand_id():
    """Verify GarmentCreateRequest strictly rejects client-supplied brand_id."""
    with pytest.raises(ValidationError) as exc_info:
        GarmentCreateRequest(
            sku="TSH-001",
            title="Tee",
            category="t_shirt",
            fabric_properties={
                "fibre_composition": {"cotton": 1.0},
                "mechanical_stretch_pct": 0.01,
                "stretch_recovery_pct": 0.9,
                "stretch_direction": "rigid_zero",
            },
            brand_id=str(uuid4()), # type: ignore
        )
    assert "Extra inputs are not permitted" in str(exc_info.value) or "brand_id" in str(exc_info.value)


def test_measurement_record_rejects_user_id():
    """Verify MeasurementRecordRequest rejects client-supplied user_id."""
    with pytest.raises(ValidationError) as exc_info:
        MeasurementRecordRequest(
            expected_revision=1,
            measurements=[MeasurementItem(measurement_code="stature", value_cm=175.0)],
            user_id=str(uuid4()), # type: ignore
        )
    assert "Extra inputs are not permitted" in str(exc_info.value) or "user_id" in str(exc_info.value)
