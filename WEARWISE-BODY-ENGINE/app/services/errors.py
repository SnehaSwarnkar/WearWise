"""
WearWise Service Layer Exceptions
Standard exceptions mapped to HTTP error codes in the API transport layer.
"""

from typing import Optional, List, Dict, Any


class ServiceError(Exception):
    """Base exception for service layer operations."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or []


class NotFoundError(ServiceError):
    """Resource not found."""
    def __init__(self, message: str, code: str = "RESOURCE_NOT_FOUND", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message, code=code, details=details)


class ForbiddenError(ServiceError):
    """Unauthorized cross-user or cross-brand access attempt."""
    def __init__(self, message: str, code: str = "FORBIDDEN", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message, code=code, details=details)


class ConflictError(ServiceError):
    """Optimistic concurrency or duplicate resource conflict."""
    def __init__(self, message: str, code: str = "OPTIMISTIC_LOCK_CONFLICT", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message, code=code, details=details)


class ValidationError(ServiceError):
    """Input value or anatomical bound violation."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message, code=code, details=details)
