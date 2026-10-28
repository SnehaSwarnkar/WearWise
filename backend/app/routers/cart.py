"""
Cart is keyed by session_id (anonymous, stored server-side in JSON).

GET    /api/cart/{session_id}          — get cart
POST   /api/cart/add                   — add item
PUT    /api/cart/update                — change quantity
DELETE /api/cart/{session_id}/{item_id} — remove item
DELETE /api/cart/{session_id}          — clear cart
"""

from fastapi import APIRouter, HTTPException
from app.schemas.cart import (
    CartAddRequest,
    CartUpdateRequest,
    CartResponse,
    CartItem,
)
from app import database as db

router = APIRouter(prefix="/api/cart", tags=["Cart"])

SHIPPING_FREE_THRESHOLD = 2000
SHIPPING_FEE = 99


def _calc_totals(items: list[dict]) -> tuple[int, int, int]:
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in items)
    shipping = 0 if (subtotal == 0 or subtotal >= SHIPPING_FREE_THRESHOLD) else SHIPPING_FEE
    return subtotal, shipping, subtotal + shipping


@router.get("/{session_id}", response_model=CartResponse)
def get_cart(session_id: str):
    """Return the current cart for a session."""
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == session_id), None)
    items = cart["items"] if cart else []
    subtotal, shipping, total = _calc_totals(items)
    return CartResponse(
        session_id=session_id,
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@router.post("/add", response_model=CartResponse)
def add_to_cart(payload: CartAddRequest):
    """Add a product to the cart (or increment quantity if already present)."""
    carts = db.find_all("carts")
    cart_index = next(
        (i for i, c in enumerate(carts) if c["session_id"] == payload.session_id), None
    )

    if cart_index is None:
        # Create new cart
        carts.append({"session_id": payload.session_id, "items": []})
        cart_index = len(carts) - 1

    items: list[dict] = carts[cart_index]["items"]
    existing = next((it for it in items if it["id"] == payload.item.id), None)

    if existing:
        existing["quantity"] = existing.get("quantity", 1) + payload.item.quantity
    else:
        items.append(payload.item.model_dump())

    db.save("carts", carts)

    subtotal, shipping, total = _calc_totals(items)
    return CartResponse(
        session_id=payload.session_id,
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@router.put("/update", response_model=CartResponse)
def update_quantity(payload: CartUpdateRequest):
    """Update the quantity of an item in the cart."""
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == payload.session_id), None)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = next((it for it in cart["items"] if it["id"] == payload.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    if payload.quantity < 1:
        cart["items"] = [it for it in cart["items"] if it["id"] != payload.item_id]
    else:
        item["quantity"] = payload.quantity

    db.save("carts", carts)

    subtotal, shipping, total = _calc_totals(cart["items"])
    return CartResponse(
        session_id=payload.session_id,
        items=cart["items"],
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@router.delete("/{session_id}/{item_id}", response_model=CartResponse)
def remove_item(session_id: str, item_id: int):
    """Remove a single item from the cart."""
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == session_id), None)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart["items"] = [it for it in cart["items"] if it["id"] != item_id]
    db.save("carts", carts)

    subtotal, shipping, total = _calc_totals(cart["items"])
    return CartResponse(
        session_id=session_id,
        items=cart["items"],
        subtotal=subtotal,
        shipping=shipping,
        total=total,
    )


@router.delete("/{session_id}", response_model=CartResponse)
def clear_cart(session_id: str):
    """Empty the cart after checkout."""
    carts = db.find_all("carts")
    carts = [c for c in carts if c["session_id"] != session_id]
    db.save("carts", carts)
    return CartResponse(session_id=session_id, items=[], subtotal=0, shipping=0, total=0)
