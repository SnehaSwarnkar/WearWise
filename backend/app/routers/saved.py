"""
Saved Looks & Wishlist

POST   /api/saved/looks                       — save a look
GET    /api/saved/looks/{session_id}          — list saved looks
DELETE /api/saved/looks/{look_id}             — remove a look

POST   /api/saved/wishlist                    — add to wishlist
GET    /api/saved/wishlist/{session_id}       — list wishlist
DELETE /api/saved/wishlist/{item_id}          — remove from wishlist
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from app.schemas.saved import (
    SavedLook,
    WishlistItem,
    SaveLookRequest,
    SaveWishlistRequest,
)
from app import database as db

router = APIRouter(prefix="/api/saved", tags=["Saved Looks & Wishlist"])


# ── SAVED LOOKS ──────────────────────────────────────────────────────────────

@router.post("/looks", response_model=SavedLook)
def save_look(payload: SaveLookRequest):
    """Save a look to a session's collection."""
    now = datetime.now(timezone.utc).isoformat()
    look = SavedLook(
        id=str(uuid.uuid4())[:8],
        session_id=payload.session_id,
        name=payload.name,
        description=payload.description,
        image=payload.image,
        created_at=now,
    )
    db.insert("saved_looks", look.model_dump())
    return look


@router.get("/looks/{session_id}", response_model=list[SavedLook])
def list_saved_looks(session_id: str):
    """Return all saved looks for a session."""
    return [sl for sl in db.find_all("saved_looks") if sl.get("session_id") == session_id]


@router.delete("/looks/{look_id}")
def remove_look(look_id: str):
    """Remove a saved look."""
    found = db.delete_one("saved_looks", id=look_id)
    if not found:
        raise HTTPException(status_code=404, detail="Saved look not found")
    return {"detail": "Removed"}


# ── WISHLIST ──────────────────────────────────────────────────────────────────

@router.post("/wishlist", response_model=WishlistItem)
def add_to_wishlist(payload: SaveWishlistRequest):
    """Add a product to a session's wishlist (no duplicates)."""
    existing = db.find_all("wishlist")

    # Prevent duplicate for same session + product
    if any(
        w["session_id"] == payload.session_id and w["product_id"] == payload.product_id
        for w in existing
    ):
        raise HTTPException(status_code=409, detail="Product already in wishlist")

    now = datetime.now(timezone.utc).isoformat()
    item = WishlistItem(
        id=str(uuid.uuid4())[:8],
        session_id=payload.session_id,
        product_id=payload.product_id,
        name=payload.name,
        price=payload.price,
        image=payload.image,
        brand=payload.brand,
        created_at=now,
    )
    db.insert("wishlist", item.model_dump())
    return item


@router.get("/wishlist/{session_id}", response_model=list[WishlistItem])
def list_wishlist(session_id: str):
    """Return all wishlist items for a session."""
    return [w for w in db.find_all("wishlist") if w.get("session_id") == session_id]


@router.delete("/wishlist/{item_id}")
def remove_from_wishlist(item_id: str):
    """Remove an item from the wishlist."""
    found = db.delete_one("wishlist", id=item_id)
    if not found:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return {"detail": "Removed"}
