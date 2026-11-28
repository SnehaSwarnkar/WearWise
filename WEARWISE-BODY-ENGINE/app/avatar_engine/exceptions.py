"""
WearWise Avatar Engine Exception Hierarchy
Engine-specific exceptions inheriting from DomainError.
"""

from typing import Optional, Dict, Any
from app.domain.exceptions.base import DomainError


class AvatarEngineError(DomainError):
    """Base exception for all avatar engine failures."""
    pass


class EngineNotReadyError(AvatarEngineError):
    """Raised when inference or export is attempted before successful engine initialization."""
    pass


class InvalidParameterError(AvatarEngineError):
    """Raised when avatar generation parameters fail bounds or contain non-finite values."""
    pass


class MeshDeformationError(AvatarEngineError):
    """Raised when generated mesh fails structural integrity (NaNs, Infs, degeneracy)."""
    pass


class GLBExportError(AvatarEngineError):
    """Raised when glTF binary serialization fails."""
    pass
