"""
WearWise BICE Exception Hierarchy
Structured exceptions for Body Intelligence & Calibration Engine operations.
Decoupled from HTTP status codes and external framework layers.
"""

from typing import Optional, Dict, Any
from app.domain.exceptions.base import (
    DomainError,
    InvalidControlValueError,
    InvalidMeasurementError,
    InvalidShapeSpecError,
)


class BICEError(DomainError):
    """Base exception for all Body Intelligence & Calibration Engine failures."""
    pass


class BICEValidationError(BICEError, InvalidControlValueError):
    """Raised when consumer semantic controls or physical measurements fail validation."""
    pass


class BICEBoundsExceededError(BICEError):
    """Raised when generated regional shape scales exceed provisional engineering bounds."""
    pass


class BICEInsufficientSignalError(BICEError):
    """Raised when locality evaluation target region mean displacement is below 1e-4 m."""
    pass


class BICEConvergenceError(BICEError):
    """Raised when iterative shape optimization fails to converge within iteration limits."""
    pass


class BICEConfigurationError(BICEError):
    """Raised when an invalid BICE configuration or unknown mapping version is specified."""
    pass
