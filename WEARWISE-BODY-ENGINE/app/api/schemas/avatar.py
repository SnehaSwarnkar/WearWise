"""
Pydantic Schemas for 3D Avatar Generation & Asset Delivery
"""

from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


class GenerateAvatarRequest(BaseModel):
    profile_id: uuid.UUID
    rigged: bool = False


class AvatarGenerationResponse(BaseModel):
    avatar_id: str
    profile_id: str
    profile_revision: int
    asset_url: str
    format: str = "glb"
    size_bytes: int
    sha256_checksum: str
    generation_duration_ms: float
    vertex_count: int
    triangle_count: Optional[int] = None
    is_valid_manifold: bool
    status: str = "completed"
    extracted_measurements: Dict[str, Any]


class AvatarStatusResponse(BaseModel):
    avatar_id: str
    profile_id: str
    format: str
    size_bytes: int
    sha256_checksum: str
    generation_duration_ms: float
    vertex_count: int
    triangle_count: Optional[int] = None
    is_valid_manifold: bool
    status: str
    engine_metadata: Dict[str, Any]
