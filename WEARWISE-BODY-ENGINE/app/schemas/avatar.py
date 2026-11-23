"""
WearWise Avatar Transport Schemas
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AvatarGenerateRequest(BaseModel):
    """Request to trigger avatar generation. user_id is forbidden (derived from auth principal)."""
    model_config = ConfigDict(extra="forbid")

    profile_id: UUID


class AvatarStatusResponse(BaseModel):
    avatar_id: UUID
    status: str
    format: str = "glb"
    vertex_count: int
    face_count: int
    is_valid_manifold: bool
    download_url: str
    generation_duration_ms: float
    created_at: datetime
