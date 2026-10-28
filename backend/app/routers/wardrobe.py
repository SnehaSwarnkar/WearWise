"""
POST   /api/wardrobe/upload            — upload one or more clothing images
GET    /api/wardrobe/{session_id}      — list wardrobe items (optional ?category=)
PATCH  /api/wardrobe/{item_id}         — rename or re-categorise an item
DELETE /api/wardrobe/{item_id}         — delete a wardrobe item
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from app.schemas.wardrobe import WardrobeItem, WardrobeItemUpdate
from app import database as db

router = APIRouter(prefix="/api/wardrobe", tags=["Wardrobe"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "wardrobe"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
VALID_CATEGORIES = {"Tops", "Bottoms", "Dresses", "Shoes", "Accessories"}


@router.post("/upload", response_model=list[WardrobeItem])
async def upload_clothes(
    session_id: str = Form(...),
    category: str = Form("Tops"),
    files: list[UploadFile] = File(...),
):
    """Upload one or more clothing images to a user's wardrobe."""
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of {VALID_CATEGORIES}")

    saved_items = []
    now = datetime.now(timezone.utc).isoformat()

    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' is not an allowed image type (JPEG, PNG, WEBP).",
            )

        ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        dest = UPLOAD_DIR / filename

        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)

        item = WardrobeItem(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            name=file.filename or filename,
            category=category,
            image_url=f"/uploads/wardrobe/{filename}",
            created_at=now,
        )
        db.insert("wardrobe", item.model_dump())
        saved_items.append(item)

    return saved_items


@router.get("/{session_id}", response_model=list[WardrobeItem])
def list_wardrobe(
    session_id: str,
    category: str | None = Query(None, description="Filter by category"),
):
    """Return all wardrobe items for a session, optionally filtered by category."""
    items = [w for w in db.find_all("wardrobe") if w.get("session_id") == session_id]
    if category and category != "All":
        items = [w for w in items if w.get("category") == category]
    return items


@router.patch("/{item_id}", response_model=WardrobeItem)
def update_wardrobe_item(item_id: str, payload: WardrobeItemUpdate):
    """Rename or re-categorise a wardrobe item."""
    all_items = db.find_all("wardrobe")
    item = next((w for w in all_items if w["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = payload.model_dump(exclude_none=True)
    if "category" in updates and updates["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Category must be one of {VALID_CATEGORIES}")

    updated = db.update_one("wardrobe", {"id": item_id}, updates)
    return updated


@router.delete("/{item_id}")
def delete_wardrobe_item(item_id: str):
    """Delete a wardrobe item and its image file."""
    all_items = db.find_all("wardrobe")
    item = next((w for w in all_items if w["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Remove the file from disk
    if item.get("image_url"):
        file_path = Path(__file__).parent.parent.parent / item["image_url"].lstrip("/")
        if file_path.exists():
            file_path.unlink()

    db.delete_one("wardrobe", id=item_id)
    return {"detail": "Deleted successfully"}
