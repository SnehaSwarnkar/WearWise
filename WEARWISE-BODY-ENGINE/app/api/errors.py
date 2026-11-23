"""
WearWise API Error Envelopes & Exception Handlers
Formats all errors conforming strictly to API_CONTRACTS.md Section 2 Standard Error Envelope.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from app.services.errors import (
    ServiceError,
    NotFoundError,
    ForbiddenError,
    ConflictError,
    ValidationError,
)


def make_error_envelope(
    code: str,
    message: str,
    status_code: int,
    details: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generates canonical standard error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or [],
        }
    }


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Handles service layer errors."""
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ForbiddenError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    content = make_error_envelope(
        code=exc.code,
        message=exc.message,
        status_code=status_code,
        details=exc.details,
    )
    return JSONResponse(status_code=status_code, content=content)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic request validation errors."""
    details = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        details.append({"field": loc, "issue": msg})

    content = make_error_envelope(
        code="REQUEST_VALIDATION_ERROR",
        message="Request payload validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)
