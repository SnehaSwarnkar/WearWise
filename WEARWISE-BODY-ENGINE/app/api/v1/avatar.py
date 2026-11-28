"""
FastAPI Router for Avatar Generation and Asset Delivery
Endpoint base: /api/v1/avatar
"""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Response, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.auth import get_current_user_id
from app.services.avatar_service import AvatarOrchestrationService
from app.api.schemas.avatar import (
    GenerateAvatarRequest,
    AvatarGenerationResponse,
    AvatarStatusResponse,
)

router = APIRouter(prefix="/avatar", tags=["3D Avatar Engine"])


@router.post("/generate", response_model=AvatarGenerationResponse)
def generate_avatar(
    payload: GenerateAvatarRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Generates a 3D avatar mesh from profile revision using NAVER Anny adapter,
    saves the GLB into content-addressable storage, extracts anthropometry,
    and updates active measurements.
    """
    srv = AvatarOrchestrationService(db)
    result = srv.generate_avatar_for_profile(
        profile_id=payload.profile_id,
        requesting_user_id=user_id,
        rigged=payload.rigged,
    )
    db.commit()
    return result


@router.get("/{avatar_id}/status", response_model=AvatarStatusResponse)
def get_avatar_status(
    avatar_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Retrieves avatar asset generation status and mesh validation metrics."""
    srv = AvatarOrchestrationService(db)
    return srv.get_avatar_status(avatar_id=avatar_id, requesting_user_id=user_id)


@router.get("/assets/{avatar_id}.glb")
def get_avatar_glb(
    avatar_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    if_none_match: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Streams private binary glTF 2.0 payload.
    Ownership is evaluated before checking conditional caching headers.
    """
    srv = AvatarOrchestrationService(db)
    asset_model, glb_bytes = srv.get_avatar_asset(
        asset_id=avatar_id,
        requesting_user_id=user_id,
    )

    etag = f'"{asset_model.sha256_checksum}"'
    if if_none_match and if_none_match.strip() == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    return Response(
        content=glb_bytes,
        media_type="model/gltf-binary",
        headers={
            "Cache-Control": "private, no-store",
            "ETag": etag,
            "Content-Length": str(len(glb_bytes)),
        },
    )
