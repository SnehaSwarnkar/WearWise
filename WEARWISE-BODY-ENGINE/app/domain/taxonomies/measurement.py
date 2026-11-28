"""
WearWise Anthropometric Measurement Taxonomies
Orthogonal classifications separating data origin, scientific validity, persistence lifecycle, and sizing assessment.
"""

from enum import Enum


class MeasurementAcquisitionMethod(str, Enum):
    """How the physical measurement value was originally captured."""
    USER_REPORTED = "user_reported"          # Unverified self-report by user
    TAPE_MEASURED = "tape_measured"          # Measured by customer with physical tape measure
    GEOMETRY_EXTRACTED = "geometry_extracted" # Computed algorithmically from 3D mesh surface
    MODEL_ESTIMATED = "model_estimated"      # Statistically derived from demographic/height priors


class MeasurementValidationState(str, Enum):
    """The formal scientific verification status of the measurement value."""
    UNVALIDATED = "unvalidated"              # No external verification performed
    INTERNALLY_CONSISTENT = "internally_consistent" # Passes anatomical consistency checks
    EXTERNALLY_VALIDATED = "externally_validated"   # Validated in controlled ground-truth study (Phase 8)
    DISPUTED = "disputed"                    # Conflicts with other authoritative measurements


class MeasurementLifecycleStatus(str, Enum):
    """Database persistence and active lifecycle state."""
    ACTIVE = "active"             # Current active measurement in profile revision
    SUPERSEDED = "superseded"     # Historical record superseded by newer revision
    DRAFT = "draft"               # In-progress entry not yet finalized
    PURGED = "purged"             # Soft-deleted / flagged for purge


class MeasurementAssessmentState(str, Enum):
    """Apparel sizing eligibility state for Honest Fit evaluation."""
    ELIGIBLE = "eligible"         # Fully assessed and valid for sizing calculations
    PROVISIONAL = "provisional"   # Geometry-extracted from provisional landmark
    UNASSESSED = "unassessed"     # Landmark not measured or evaluated
    REJECTED = "rejected"         # Rejected due to anatomical impossibility or extraction failure
