"""
WearWise Domain Exception Hierarchy
Structured exception classes for domain invariant violations (no HTTP status codes in domain layer).
"""

from typing import Optional, Dict, Any


class DomainError(Exception):
    """Base class for all WearWise domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvariantViolationError(DomainError):
    """Raised when an operation or entity constructor violates a core domain invariant."""
    pass


class InvalidMeasurementError(InvariantViolationError):
    """Raised when a body measurement value, unit, tolerance, or reliability weight is invalid."""
    pass


class InvalidControlValueError(InvariantViolationError):
    """Raised when a semantic slider control value is out of bounds [0.0, 1.0] or non-finite."""
    pass


class InvalidShapeSpecError(InvariantViolationError):
    """Raised when AvatarShapeSpec attributes or regional scales fail invariant checks."""
    pass


class UnsupportedOperationError(DomainError):
    """Raised when an unsupported operation or deferred dimension is invoked in the domain layer."""
    pass
