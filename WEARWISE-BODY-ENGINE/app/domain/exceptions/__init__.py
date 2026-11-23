"""
WearWise Domain Exceptions
"""

from app.domain.exceptions.base import (
    DomainError,
    InvariantViolationError,
    InvalidMeasurementError,
    InvalidControlValueError,
    InvalidShapeSpecError,
    UnsupportedOperationError,
)

__all__ = [
    "DomainError",
    "InvariantViolationError",
    "InvalidMeasurementError",
    "InvalidControlValueError",
    "InvalidShapeSpecError",
    "UnsupportedOperationError",
]
