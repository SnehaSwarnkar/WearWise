"""
POST /api/orders/place          — place an order (reads cart, clears it, returns order)
GET  /api/orders/my             — list orders for the authenticated user (Bearer token)
GET  /api/orders/{session_id}   — list orders by session ID (legacy / anonymous)
GET  /api/orders/detail/{id}    — single order detail (auth-protected)
"""

from datetime import datetime, timezone
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional

from app.core.security import (
    CANONICAL_DEFAULT_BRAND_ID,
    get_optional_authenticated_user,
    require_shopper,
)
from app.routers.products import resolve_catalog_item
from app.schemas.orders import PlaceOrderRequest, OrderResponse
from app import database as db

router = APIRouter(prefix="/api/orders", tags=["Orders"])

SHIPPING_FREE_THRESHOLD = 2000
SHIPPING_FEE = 99


# ── routes ────────────────────────────────────────────────────────────────────

def _validate_customer(c) -> None:
    required_fields = ["firstName", "lastName", "email", "phone", "address", "city", "state", "pincode"]
    for f in required_fields:
        if not str(getattr(c, f, "") or "").strip():
            raise HTTPException(status_code=400, detail=f"Missing required customer field: {f}")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", c.email.strip()):
        raise HTTPException(status_code=400, detail="Invalid email address")
    digits = re.sub(r"\D", "", c.phone)
    if len(digits) < 7:
        raise HTTPException(status_code=400, detail="Invalid phone number (minimum 7 digits)")
    if len(c.pincode.strip()) < 4:
        raise HTTPException(status_code=400, detail="Invalid pincode/postal code")


def _order_to_response(order: dict) -> OrderResponse:
    excluded = {"session_id", "user_id", "idempotency_key"}
    return OrderResponse(**{k: v for k, v in order.items() if k not in excluded})


@router.post("/place", response_model=OrderResponse)
def place_order(
    payload: PlaceOrderRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """
    Read the session cart, validate customer & catalog pricing, create an idempotent
    demo order record, clear the cart, and return the confirmed order.
    """
    if payload.paymentMethod not in ("upi", "card", "cod"):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    auth_user = get_optional_authenticated_user(request, authorization)
    if auth_user and auth_user.get("role") == "seller":
        raise HTTPException(status_code=403, detail="Seller accounts cannot place shopper orders.")

    _validate_customer(payload.customer)

    # Idempotency check: prevent duplicate orders on double-submit or retry
    if payload.idempotency_key:
        existing_order = next(
            (
                o for o in db.find_all("orders")
                if o.get("idempotency_key") == payload.idempotency_key
                and o.get("session_id") == payload.session_id
            ),
            None,
        )
        if existing_order:
            return _order_to_response(existing_order)

    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == payload.session_id), None)

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    user_id = auth_user["id"] if auth_user else None

    # Re-resolve authoritative catalog prices, seller brand attribution & revisions for every cart item
    items = []
    for raw_it in cart["items"]:
        it = dict(raw_it)
        resolved = resolve_catalog_item(sku=it.get("sku"), item_id=it.get("id"), size=it.get("size"))
        if it.get("sku") and not resolved:
            raise HTTPException(status_code=400, detail=f"Product SKU '{it.get('sku')}' is no longer available in catalog.")
        if resolved:
            it["price"] = int(resolved["price"])
            it["name"] = resolved["name"]
            it["published_revision"] = resolved.get("published_revision")
            it["seller_brand_id"] = resolved.get("brand_id") or CANONICAL_DEFAULT_BRAND_ID
        items.append(it)

    subtotal = sum(it["price"] * it.get("quantity", 1) for it in items)
    shipping = 0 if subtotal >= SHIPPING_FREE_THRESHOLD else SHIPPING_FEE
    total = subtotal + shipping

    now = datetime.now(timezone.utc).isoformat()
    order_id = f"WW{datetime.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    order = {
        "id": order_id,
        "session_id": payload.session_id,
        "user_id": user_id,
        "idempotency_key": payload.idempotency_key,
        "items": items,
        "customer": payload.customer.model_dump(),
        "paymentMethod": payload.paymentMethod,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "createdAt": now,
        "status": "Confirmed",
        "is_demo_checkout": True,
        "payment_status": "DEMO_NO_PAYMENT_CAPTURED",
    }

    db.insert("orders", order)

    # Clear the cart
    remaining_carts = [c for c in carts if c["session_id"] != payload.session_id]
    db.save("carts", remaining_carts)

    return _order_to_response(order)


@router.get("/my", response_model=list[OrderResponse])
def list_my_orders(user: dict = Depends(require_shopper)):
    """
    Return all orders for the authenticated shopper (identified via cookie or Bearer token).
    """
    all_orders = db.find_all("orders")

    # Orders explicitly tied to this user_id
    user_orders = [o for o in all_orders if o.get("user_id") == user["id"]]

    # Deduplicate by order id
    seen_ids = {o["id"] for o in user_orders}
    unique_orders = user_orders + [
        o for o in all_orders
        if o["id"] not in seen_ids and o.get("user_id") is None
        # Only include session-only orders if customer email matches (best-effort link)
        and o.get("customer", {}).get("email", "").lower() == user["email"].lower()
    ]

    # Sort newest first
    unique_orders.sort(key=lambda o: o.get("createdAt", ""), reverse=True)

    return [
        OrderResponse(**{k: v for k, v in o.items() if k not in ("session_id", "user_id")})
        for o in unique_orders
    ]


@router.get("/{session_id}", response_model=list[OrderResponse])
def list_orders(session_id: str):
    """Return all orders placed in this session (legacy anonymous endpoint)."""
    all_orders = db.find_all("orders")
    session_orders = [o for o in all_orders if o.get("session_id") == session_id]
    session_orders.sort(key=lambda o: o.get("createdAt", ""), reverse=True)
    return [OrderResponse(**{k: v for k, v in o.items() if k not in ("session_id", "user_id")}) for o in session_orders]


@router.get("/detail/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_session_id: Optional[str] = Header(default=None),
):
    """
    Return a specific order by its ID, restricted to the owning shopper or session.
    """
    all_orders = db.find_all("orders")
    order = next((o for o in all_orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    user = get_optional_authenticated_user(request, authorization)
    if user:
        if user.get("role") == "seller":
            raise HTTPException(status_code=403, detail="Use Seller Orders endpoint to inspect seller orders.")
        belongs = (
            order.get("user_id") == user["id"]
            or (order.get("user_id") is None and order.get("customer", {}).get("email", "").lower() == user["email"].lower())
        )
        if not belongs:
            raise HTTPException(status_code=403, detail="Access denied")
        return _order_to_response(order)

    if x_session_id and order.get("session_id") == x_session_id:
        return _order_to_response(order)

    raise HTTPException(status_code=403, detail="Access denied: authentication or matching session required")
