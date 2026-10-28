"""
POST /api/avatar/save           — save manual or AI-assisted avatar profile
GET  /api/avatar/{session_id}   — fetch a session's latest avatar profile
POST /api/avatar/analyze-photo  — AI-assisted mode: accept photo upload, return starter profile
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.avatar import AvatarProfile, AvatarProfileResponse
from app import database as db

router = APIRouter(prefix="/api/avatar", tags=["Avatar & Style Profile"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/save", response_model=AvatarProfileResponse)
def save_avatar(payload: AvatarProfile):
    """
    Persist a completed manual or AI-assisted style profile.
    If a profile already exists for the session it is replaced.
    """
    now = datetime.now(timezone.utc).isoformat()
    profile_id = str(uuid.uuid4())[:8]

    record = {
        **payload.model_dump(),
        "id": profile_id,
        "createdAt": now,
    }

    # Remove any previous profile for this session
    existing = db.find_all("avatar_profiles")
    updated = [p for p in existing if p.get("session_id") != payload.session_id]
    updated.append(record)
    db.save("avatar_profiles", updated)

    return AvatarProfileResponse(**record)


@router.get("/{session_id}", response_model=AvatarProfileResponse | None)
def get_avatar(session_id: str):
    """Fetch the latest saved style profile for a session."""
    all_profiles = db.find_all("avatar_profiles")
    profile = next(
        (p for p in reversed(all_profiles) if p.get("session_id") == session_id),
        None,
    )
    if not profile:
        return None
    return AvatarProfileResponse(**profile)


@router.post("/analyze-photo")
async def analyze_photo(
    session_id: str = Form(...),
    selected_colour: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """
    AI-assisted mode: accept a photo upload and return a suggested starter profile.
    Currently returns a rule-based recommendation.
    Swap the body for real CV/ML logic when ready.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG or WEBP images are allowed.")

    # Save the uploaded file
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    dest = UPLOAD_DIR / filename
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    # ---------- Simulated AI analysis ----------
    # In production: run a colour-analysis model on `contents` and return real values.
    suggested_profile = {
        "mode": "ai",
        "colour": "warm",
        "bodyType": "rectangle",
        "fit": "Relaxed",
        "styles": ["Casual", "Minimal"],
        "selectedColour": selected_colour or "#ff3b91",
        "photo_url": f"/uploads/avatars/{filename}",
        "ai_note": (
            "Based on your photo, warm earthy tones suit you best. "
            "We've detected a balanced silhouette — a rectangle body profile — "
            "and recommend relaxed, minimal styles to complement your natural shape."
        ),
    }
    # -------------------------------------------

    return suggested_profile
