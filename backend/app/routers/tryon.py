"""
Virtual Try-On flow

POST /api/tryon/upload-photo   — Step 1: upload user photo, get a session reference
POST /api/tryon/process        — Step 2: apply a chosen look to the stored photo
GET  /api/tryon/{session_id}   — fetch the result for a session
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app import database as db

router = APIRouter(prefix="/api/tryon", tags=["Virtual Try-On"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "tryon"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload-photo")
async def upload_photo(
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Step 1 — Accept the user's photo.
    Returns a photo_id that is used in the /process call.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG or WEBP images are allowed.")

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    dest = UPLOAD_DIR / filename

    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    photo_id = str(uuid.uuid4())[:8]
    record = {
        "photo_id": photo_id,
        "session_id": session_id,
        "photo_url": f"/uploads/tryon/{filename}",
        "status": "uploaded",
        "result_url": None,
        "look": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("tryon_sessions", record)

    return {"photo_id": photo_id, "photo_url": f"/uploads/tryon/{filename}"}


@router.post("/process")
def process_tryon(
    session_id: str = Form(...),
    photo_id: str = Form(...),
    look_id: int = Form(...),
    look_name: str = Form(...),
):
    """
    Step 2 — Apply the chosen look to the uploaded photo.
    Currently simulates processing. In production, call your AI try-on model here.
    """
    all_sessions = db.find_all("tryon_sessions")
    record = next(
        (r for r in all_sessions if r["photo_id"] == photo_id and r["session_id"] == session_id),
        None,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Photo session not found")

    # ── Simulated AI try-on ──────────────────────────────────────────────────
    # In production: send record["photo_url"] + look details to your model,
    # get back a composed result image URL, and store it below.
    simulated_result_url = record["photo_url"]  # Echo the original for now
    # ─────────────────────────────────────────────────────────────────────────

    updated = db.update_one(
        "tryon_sessions",
        {"photo_id": photo_id},
        {
            "status": "completed",
            "result_url": simulated_result_url,
            "look": {"id": look_id, "name": look_name},
        },
    )

    return {
        "photo_id": photo_id,
        "look": {"id": look_id, "name": look_name},
        "result_url": simulated_result_url,
        "status": "completed",
    }


@router.get("/{session_id}")
def get_tryon_result(session_id: str):
    """Return the latest try-on result for a session."""
    all_sessions = db.find_all("tryon_sessions")
    session_records = [r for r in all_sessions if r.get("session_id") == session_id]
    if not session_records:
        raise HTTPException(status_code=404, detail="No try-on session found")
    # Return the most recent
    return sorted(session_records, key=lambda r: r["created_at"])[-1]
