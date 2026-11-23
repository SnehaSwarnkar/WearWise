"""
WearWise API Error Envelope Schemas
Standardized error envelopes for REST responses.
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: List[ErrorDetail] = Field(default_factory=list)


class StandardErrorEnvelope(BaseModel):
    error: ErrorBody
