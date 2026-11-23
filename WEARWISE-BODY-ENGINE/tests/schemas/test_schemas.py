"""
Test Suite: Pydantic v2 Transport Schemas Validation
Verifies request and response schema parsing, range validations, and envelope structures.
"""

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError

from app.schemas.profile import ProfileCreateRequest, ProfileResponse
from app.schemas.measurement import MeasurementItem, MeasurementRecordRequest
from app.schemas.control import ControlsUpdateRequest, ControlsResponse
from app.schemas.avatar import AvatarGenerateRequest, AvatarStatusResponse
from app.schemas.garment import (
    FabricPropertiesSchema,
    GarmentCreateRequest,
    GarmentSizeCreateRequest,
    GarmentMeasurementItem,
)
from app.schemas.fit import FitRecommendRequest, FitRecommendResponse, RegionalComparisonResponse
from app.schemas.error import StandardErrorEnvelope, ErrorBody, ErrorDetail


def test_profile_create_request_validation():
    """Verify ProfileCreateRequest validates stature bounds [100.0, 230.0]."""
    req = ProfileCreateRequest(
        presentation_gender="masculine",
        stature_cm=178.50,
        reported_weight_kg=74.0,
        initial_controls=ControlsUpdateRequest(shoulder_width=0.60),
    )
    assert req.presentation_gender == "masculine"
    assert req.stature_cm == 178.50
    assert req.initial_controls.shoulder_width == 0.60

    # Test out of bounds stature
    with pytest.raises(ValidationError):
        ProfileCreateRequest(presentation_gender="masculine", stature_cm=99.0)

    with pytest.raises(ValidationError):
        ProfileCreateRequest(presentation_gender="masculine", stature_cm=231.0)


def test_measurement_record_request():
    """Verify measurement recording request structure."""
    item = MeasurementItem(
        measurement_code="chest_circumference",
        value_cm=104.5,
        unit="cm",
        acquisition_method="tape_measured",
        tolerance_cm=1.0,
    )
    req = MeasurementRecordRequest(expected_revision=1, measurements=[item])
    assert req.expected_revision == 1
    assert len(req.measurements) == 1

    # Invalidate negative value
    with pytest.raises(ValidationError):
        MeasurementItem(measurement_code="chest", value_cm=-5.0)


def test_garment_create_request():
    """Verify garment creation and fabric stretch validation."""
    fab = FabricPropertiesSchema(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.015,
        stretch_recovery_pct=0.90,
        stretch_direction="rigid_zero",
    )
    req = GarmentCreateRequest(
        sku="TSH-001",
        title="Classic Tee",
        category="t_shirt",
        fabric_properties=fab,
    )
    assert req.sku == "TSH-001"
    assert req.fabric_properties.mechanical_stretch_pct == 0.015


def test_fit_recommend_schemas():
    """Verify fit recommendation request and response."""
    pid = uuid4()
    gid = uuid4()
    req = FitRecommendRequest(profile_id=pid, garment_id=gid, user_fit_preference="regular")
    assert req.profile_id == pid

    comp = RegionalComparisonResponse(
        region="chest",
        body_measurement_cm=104.5,
        garment_dimension_cm=112.0,
        ease_cm=7.5,
        classification="regular",
        explanation="Standard comfortable room.",
    )
    res = FitRecommendResponse(
        recommendation_id=uuid4(),
        garment_id=gid,
        recommended_size="L",
        composite_fit_score=94.5,
        coverage_ratio=1.0,
        status="ready",
        regional_comparisons=[comp],
        disclaimer="Sample score",
    )
    assert res.composite_fit_score == 94.5


def test_standard_error_envelope():
    """Verify standard error envelope serialization."""
    env = StandardErrorEnvelope(
        error=ErrorBody(
            code="MEASUREMENT_OUT_OF_BOUNDS",
            message="Invalid dimension",
            status_code=422,
            details=[ErrorDetail(field="stature_cm", issue="Must be >= 100.0")],
        )
    )
    d = env.model_dump()
    assert d["error"]["code"] == "MEASUREMENT_OUT_OF_BOUNDS"
    assert d["error"]["details"][0]["field"] == "stature_cm"
