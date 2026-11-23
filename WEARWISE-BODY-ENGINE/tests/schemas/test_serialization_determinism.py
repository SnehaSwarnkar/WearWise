"""
Test Suite: Serialization Determinism
Verifies that domain entities and Pydantic schemas serialize and round-trip deterministically.
"""

from decimal import Decimal
import json
from uuid import uuid4
import pytest

from app.domain.entities.body import BodyProfile, BodyMeasurement, BodyShapeControls
from app.domain.entities.avatar import RegionalShapeScale, AvatarShapeSpec
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import PresentationGender
from app.schemas.profile import ProfileCreateRequest
from app.schemas.control import ControlsUpdateRequest


def test_body_shape_controls_determinism():
    """Verify that equivalent slider states serialize to identical dictionaries and JSON."""
    c1 = BodyShapeControls(shoulder_width=0.45, chest_fullness=0.60)
    c2 = BodyShapeControls(shoulder_width=0.45, chest_fullness=0.60)

    d1 = c1.to_dict()
    d2 = c2.to_dict()
    assert d1 == d2
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


def test_avatar_shape_spec_determinism():
    """Verify AvatarShapeSpec determinism."""
    reg = {"shoulders": RegionalShapeScale(scale_x=0.1, scale_y=0.0, scale_z=0.0)}
    spec1 = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=180.0,
        target_measurements={"chest_circumference": 105.0},
        regional_scales=reg,
    )
    spec2 = AvatarShapeSpec(
        spec_version="1.2.1",
        presentation=PresentationGender.MASCULINE,
        target_stature_cm=180.0,
        target_measurements={"chest_circumference": 105.0},
        regional_scales=reg,
    )
    assert spec1 == spec2


def test_pydantic_schema_roundtrip_determinism():
    """Verify Pydantic model serialization and re-parsing produce identical model dumps."""
    req = ProfileCreateRequest(
        presentation_gender="masculine",
        stature_cm=178.50,
        reported_weight_kg=74.0,
        initial_controls=ControlsUpdateRequest(shoulder_width=0.55, chest_fullness=0.50),
    )
    json_str = req.model_dump_json()
    req_parsed = ProfileCreateRequest.model_validate_json(json_str)
    assert req.model_dump() == req_parsed.model_dump()
