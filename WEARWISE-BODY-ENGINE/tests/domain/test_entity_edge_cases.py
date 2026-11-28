"""
Test Suite: Domain Entity Invariant Edge Cases
Covers constructor invariant branches for LandmarkData, RegionalDisplacementSummary, ShapeEvaluationResult, ProfileRevision, GarmentProfile, GarmentSize, GarmentMeasurement, and FabricProperties.
"""

from decimal import Decimal
from uuid import uuid4
import pytest
import numpy as np

from app.domain.entities.body import BodyProfile, ProfileRevision, BodyMeasurement
from app.domain.entities.avatar import (
    RegionalShapeScale,
    AvatarShapeSpec,
    MeshData,
    LandmarkData,
    RegionalDisplacementSummary,
    ShapeEvaluationResult,
)
from app.domain.entities.garment import (
    FabricProperties,
    GarmentProfile,
    GarmentRevision,
    GarmentSize,
    GarmentMeasurement,
    FitRecommendation,
)
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import PresentationGender, FabricStretchDirection
from app.domain.exceptions.base import (
    InvalidMeasurementError,
    InvalidShapeSpecError,
    InvariantViolationError,
)


def test_landmark_data_edge_cases():
    """Verify LandmarkData constructor invariants."""
    # Empty code
    with pytest.raises(InvariantViolationError):
        LandmarkData(landmark_code="", point_3d_m=(0.0, 0.0, 0.0), anatomical_region="torso")

    # Wrong length
    with pytest.raises(InvariantViolationError):
        LandmarkData(landmark_code="c7", point_3d_m=(0.0, 0.0), anatomical_region="torso") # type: ignore

    # Non-finite coordinates
    with pytest.raises(InvariantViolationError):
        LandmarkData(landmark_code="c7", point_3d_m=(float("nan"), 0.0, 0.0), anatomical_region="torso")

    # Empty anatomical region
    with pytest.raises(InvariantViolationError):
        LandmarkData(landmark_code="c7", point_3d_m=(0.0, 0.0, 0.0), anatomical_region="")


def test_regional_displacement_summary_edge_cases():
    """Verify RegionalDisplacementSummary constructor invariants."""
    with pytest.raises(InvariantViolationError):
        RegionalDisplacementSummary(region_code="", mean_displacement_m=0.01, max_displacement_m=0.02, vertex_count=10)

    with pytest.raises(InvariantViolationError):
        RegionalDisplacementSummary(region_code="torso", mean_displacement_m=-0.01, max_displacement_m=0.02, vertex_count=10)

    with pytest.raises(InvariantViolationError):
        RegionalDisplacementSummary(region_code="torso", mean_displacement_m=0.01, max_displacement_m=-0.02, vertex_count=10)

    with pytest.raises(InvariantViolationError):
        RegionalDisplacementSummary(region_code="torso", mean_displacement_m=0.01, max_displacement_m=0.02, vertex_count=-1)


def test_shape_evaluation_result_edge_cases():
    """Verify ShapeEvaluationResult constructor invariants."""
    with pytest.raises(InvariantViolationError):
        ShapeEvaluationResult(
            metric_version="",
            evaluation_status="success",
            regional_displacements={},
            target_region_mean_m=0.01,
            max_non_target_mean_m=0.005,
            rmsr=0.5,
            pvsr=0.8,
            is_plausible=True,
            diagnostic_notes="",
        )

    with pytest.raises(InvariantViolationError):
        ShapeEvaluationResult(
            metric_version="1.2.1",
            evaluation_status="invalid_status",
            regional_displacements={},
            target_region_mean_m=0.01,
            max_non_target_mean_m=0.005,
            rmsr=0.5,
            pvsr=0.8,
            is_plausible=True,
            diagnostic_notes="",
        )

    with pytest.raises(InvariantViolationError):
        ShapeEvaluationResult(
            metric_version="1.2.1",
            evaluation_status="success",
            regional_displacements={},
            target_region_mean_m=-0.01,
            max_non_target_mean_m=0.005,
            rmsr=0.5,
            pvsr=0.8,
            is_plausible=True,
            diagnostic_notes="",
        )

    with pytest.raises(InvariantViolationError):
        ShapeEvaluationResult(
            metric_version="1.2.1",
            evaluation_status="success",
            regional_displacements={},
            target_region_mean_m=0.01,
            max_non_target_mean_m=0.005,
            rmsr=-0.5,
            pvsr=0.8,
            is_plausible=True,
            diagnostic_notes="",
        )


def test_body_measurement_enum_invariants():
    """Verify BodyMeasurement rejects invalid taxonomy types."""
    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal("170.0"),
            acquisition_method="untyped_string", # type: ignore
        )

    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal("170.0"),
            validation_state="untyped_string", # type: ignore
        )

    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal("170.0"),
            lifecycle_status="untyped_string", # type: ignore
        )

    with pytest.raises(InvalidMeasurementError):
        BodyMeasurement(
            measurement_code="stature",
            value_cm=Decimal("170.0"),
            assessment_state="untyped_string", # type: ignore
        )


def test_profile_revision_invariants():
    """Verify ProfileRevision invariants."""
    rev = ProfileRevision(profile_id=uuid4(), revision_number=1)
    assert rev.revision_number == 1

    with pytest.raises(InvariantViolationError):
        ProfileRevision(profile_id=uuid4(), revision_number=0)


def test_garment_entities_invariants():
    """Verify GarmentProfile, GarmentRevision, GarmentSize, and GarmentMeasurement invariants."""
    # GarmentMeasurement
    with pytest.raises(InvariantViolationError):
        GarmentMeasurement(dimension_code="", value_cm=Decimal("10.0"))

    with pytest.raises(InvariantViolationError):
        GarmentMeasurement(dimension_code="chest", value_cm=Decimal("0.0"))

    with pytest.raises(InvariantViolationError):
        GarmentMeasurement(dimension_code="chest", value_cm=Decimal("10.0"), tolerance_cm=Decimal("-0.5"))

    # GarmentSize
    with pytest.raises(InvariantViolationError):
        GarmentSize(size_label="")

    # GarmentRevision
    fab = FabricProperties(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.01,
        stretch_recovery_pct=0.9,
        stretch_direction=FabricStretchDirection.RIGID_ZERO,
    )
    with pytest.raises(InvariantViolationError):
        GarmentRevision(revision_number=0, fabric_properties=fab)

    # GarmentProfile
    with pytest.raises(InvariantViolationError):
        GarmentProfile(brand_id=uuid4(), sku="", title="Tee", category="t_shirt")

    with pytest.raises(InvariantViolationError):
        GarmentProfile(brand_id=uuid4(), sku="SKU1", title="", category="t_shirt")

    with pytest.raises(InvariantViolationError):
        GarmentProfile(brand_id=uuid4(), sku="SKU1", title="Tee", category="")

    with pytest.raises(InvariantViolationError):
        GarmentProfile(brand_id=uuid4(), sku="SKU1", title="Tee", category="t_shirt", current_revision=0)

    # FitRecommendation
    with pytest.raises(InvariantViolationError):
        FitRecommendation(
            profile_revision_id=uuid4(),
            garment_revision_id=uuid4(),
            recommended_size="",
            composite_score=90.0,
            coverage_ratio=1.0,
        )

    with pytest.raises(InvariantViolationError):
        FitRecommendation(
            profile_revision_id=uuid4(),
            garment_revision_id=uuid4(),
            recommended_size="L",
            composite_score=90.0,
            coverage_ratio=-0.1,
        )
