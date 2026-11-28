"""
Test Suite: Domain Taxonomies Isolation
Verifies that all 4 measurement taxonomies are strictly orthogonal and distinct enums.
"""

import pytest
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import (
    PresentationGender,
    FabricStretchDirection,
    RegionalFitClassification,
)


def test_measurement_taxonomies_orthogonality():
    """Verify that the 4 measurement taxonomies have disjoint values and independent semantics."""
    acq_values = {e.value for e in MeasurementAcquisitionMethod}
    val_values = {e.value for e in MeasurementValidationState}
    life_values = {e.value for e in MeasurementLifecycleStatus}
    assess_values = {e.value for e in MeasurementAssessmentState}

    # Verify expected members
    assert "user_reported" in acq_values
    assert "tape_measured" in acq_values
    assert "geometry_extracted" in acq_values
    assert "model_estimated" in acq_values

    assert "unvalidated" in val_values
    assert "internally_consistent" in val_values
    assert "externally_validated" in val_values
    assert "disputed" in val_values

    assert "active" in life_values
    assert "superseded" in life_values
    assert "draft" in life_values
    assert "purged" in life_values

    assert "eligible" in assess_values
    assert "provisional" in assess_values
    assert "unassessed" in assess_values
    assert "rejected" in assess_values

    # Orthogonality checks: No enum should duplicate members of another enum
    assert acq_values.isdisjoint(val_values)
    assert acq_values.isdisjoint(life_values)
    assert acq_values.isdisjoint(assess_values)
    assert val_values.isdisjoint(life_values)
    assert val_values.isdisjoint(assess_values)
    assert life_values.isdisjoint(assess_values)


def test_garment_taxonomies():
    """Verify presentation gender, fabric stretch direction, and regional fit classification."""
    assert PresentationGender.MASCULINE == "masculine"
    assert PresentationGender.FEMININE == "feminine"
    assert PresentationGender.NEUTRAL == "neutral"

    assert FabricStretchDirection.RIGID_ZERO == "rigid_zero"
    assert FabricStretchDirection.MONO_WEFT == "mono_weft"
    assert FabricStretchDirection.MONO_WARP == "mono_warp"
    assert FabricStretchDirection.BI_DIRECTIONAL_FOUR_WAY == "bi_directional_four_way"

    assert len(RegionalFitClassification) == 6
    expected_classes = {"too_tight", "fitted", "regular", "relaxed", "oversized", "too_large"}
    assert {e.value for e in RegionalFitClassification} == expected_classes
