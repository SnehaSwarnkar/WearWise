"""
Cart is keyed by session_id (anonymous, stored server-side in JSON).

GET    /api/cart/{session_id}          — get cart
POST   /api/cart/add                   — add item
PUT    /api/cart/update                — change quantity
DELETE /api/cart/{session_id}/{item_id} — remove item
DELETE /api/cart/{session_id}          — clear cart
"""

from fastapi import APIRouter, HTTPException
from app.routers.products import resolve_catalog_item
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
    """Add a product to the cart (differentiating by id AND size) with authoritative catalog pricing."""
    if payload.item.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    resolved = resolve_catalog_item(
        sku=payload.item.sku,
        item_id=payload.item.id,
        size=payload.item.size,
    )
    if payload.item.sku and not resolved:
        raise HTTPException(status_code=404, detail=f"Published product not found for SKU '{payload.item.sku}'")

    item_data = payload.item.model_dump()
    if resolved:
        item_data["id"] = resolved["id"]
        item_data["name"] = resolved["name"]
        item_data["price"] = int(resolved["price"])
        item_data["sku"] = resolved.get("sku") or item_data.get("sku")
        item_data["published_revision"] = resolved.get("published_revision")

    carts = db.find_all("carts")
    cart_index = next(
        (i for i, c in enumerate(carts) if c["session_id"] == payload.session_id), None
    )

    if cart_index is None:
        carts.append({"session_id": payload.session_id, "items": []})
        cart_index = len(carts) - 1

    items: list[dict] = carts[cart_index]["items"]
    existing = next(
        (it for it in items if it["id"] == item_data["id"] and it.get("size") == item_data.get("size")),
        None
    )

    if existing:
        existing["quantity"] = existing.get("quantity", 1) + item_data["quantity"]
        existing["price"] = item_data["price"]
        if item_data.get("published_revision") is not None:
            existing["published_revision"] = item_data["published_revision"]
    else:
        items.append(item_data)

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
    """Update the quantity of an item in the cart (optionally matching by size)."""
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == payload.session_id), None)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if payload.size is not None:
        item = next(
            (it for it in cart["items"] if it["id"] == payload.item_id and it.get("size") == payload.size),
            None,
        )
    else:
        item = next((it for it in cart["items"] if it["id"] == payload.item_id), None)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    if payload.quantity < 1:
        if payload.size is not None:
            cart["items"] = [
                it for it in cart["items"]
                if not (it["id"] == payload.item_id and it.get("size") == payload.size)
            ]
        else:
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
def remove_item(session_id: str, item_id: int, size: str | None = None):
    """Remove a single item from the cart, optionally filtering by size."""
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == session_id), None)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if size is not None:
        cart["items"] = [
            it for it in cart["items"]
            if not (it["id"] == item_id and it.get("size") == size)
        ]
    else:
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
