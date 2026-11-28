"""
Test Suite: Body Profile and Garment Entities Invariant Validation
Verifies stature bounds [100.0, 230.0], reported weight bounds, garment fabric properties, and fit recommendations.
"""

from decimal import Decimal
import pytest
from uuid import uuid4

from app.domain.entities.body import BodyProfile, ProfileRevision
from app.domain.entities.garment import (
    FabricProperties,
    GarmentProfile,
    GarmentRevision,
    GarmentSize,
    GarmentMeasurement,
    FitRecommendation,
    RegionalFitEvaluation,
)
from app.domain.taxonomies.garment import (
    PresentationGender,
    FabricStretchDirection,
    RegionalFitClassification,
)
from app.domain.exceptions.base import InvariantViolationError


def test_valid_body_profile():
    """Verify valid body profile construction."""
    uid = uuid4()
    profile = BodyProfile(
        user_id=uid,
        presentation_gender=PresentationGender.MASCULINE,
        stature_cm=Decimal("178.50"),
        reported_weight_kg=Decimal("74.00"),
    )
    assert profile.user_id == uid
    assert profile.stature_cm == Decimal("178.50")
    assert profile.current_revision == 1


@pytest.mark.parametrize("invalid_stat", [Decimal("99.9"), Decimal("230.1"), Decimal("NaN"), Decimal("Infinity")])
def test_out_of_bounds_stature(invalid_stat):
    """Verify stature bounds [100.0, 230.0] cm."""
    with pytest.raises(InvariantViolationError):
        BodyProfile(
            user_id=uuid4(),
            presentation_gender=PresentationGender.FEMININE,
            stature_cm=invalid_stat,
        )


@pytest.mark.parametrize("invalid_wt", [Decimal("29.9"), Decimal("300.1"), Decimal("NaN")])
def test_out_of_bounds_weight(invalid_wt):
    """Verify reported weight bounds [30.0, 300.0] kg."""
    with pytest.raises(InvariantViolationError):
        BodyProfile(
            user_id=uuid4(),
            presentation_gender=PresentationGender.NEUTRAL,
            stature_cm=Decimal("170.0"),
            reported_weight_kg=invalid_wt,
        )


def test_fabric_properties_rigid_zero_invariant():
    """Verify that rigid_zero requires mechanical stretch < 2%."""
    # Valid rigid_zero (< 2%)
    valid_fab = FabricProperties(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.015,
        stretch_recovery_pct=0.90,
        stretch_direction=FabricStretchDirection.RIGID_ZERO,
    )
    assert valid_fab.mechanical_stretch_pct == 0.015

    # Invalid: rigid_zero with >= 2% stretch
    with pytest.raises(InvariantViolationError):
        FabricProperties(
            fibre_composition={"cotton": 0.98, "elastane": 0.02},
            mechanical_stretch_pct=0.035,
            stretch_recovery_pct=0.90,
            stretch_direction=FabricStretchDirection.RIGID_ZERO,
        )


def test_fit_recommendation_bounds():
    """Verify fit recommendation composite score bounds [0.0, 100.0]."""
    rec = FitRecommendation(
        profile_revision_id=uuid4(),
        garment_revision_id=uuid4(),
        recommended_size="L",
        composite_score=94.5,
        coverage_ratio=1.0,
    )
    assert rec.composite_score == 94.5

    with pytest.raises(InvariantViolationError):
        FitRecommendation(
            profile_revision_id=uuid4(),
            garment_revision_id=uuid4(),
            recommended_size="L",
            composite_score=101.0,
            coverage_ratio=1.0,
        )
