"""
POST /api/orders/place          — place an order (reads cart, clears it, returns order)
GET  /api/orders/my             — list orders for the authenticated user (Bearer token)
GET  /api/orders/{session_id}   — list orders by session ID (legacy / anonymous)
GET  /api/orders/detail/{id}    — single order detail (auth-protected)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.schemas.orders import PlaceOrderRequest, OrderResponse
from app import database as db

router = APIRouter(prefix="/api/orders", tags=["Orders"])

SHIPPING_FREE_THRESHOLD = 2000
SHIPPING_FEE = 99


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_token(user_id: str) -> str:
    import hashlib
    return hashlib.sha256(f"wearwise-{user_id}".encode()).hexdigest()


def _user_from_token(token: str) -> dict | None:
    for user in db.find_all("users"):
        if _make_token(user["id"]) == token:
            return user
    return None


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/place", response_model=OrderResponse)
def place_order(
    payload: PlaceOrderRequest,
    authorization: Optional[str] = Header(default=None),
):
    """
    Read the session cart, create an order record, clear the cart,
    and return the confirmed order.
    Optionally associates the order with an authenticated user.
    """
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == payload.session_id), None)

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    if payload.paymentMethod not in ("upi", "card", "cod"):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # Resolve authenticated user if token provided
    user_id = None
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
        user = _user_from_token(token)
        if user:
            user_id = user["id"]

    items = cart["items"]
    subtotal = sum(it["price"] * it.get("quantity", 1) for it in items)
    shipping = 0 if subtotal >= SHIPPING_FREE_THRESHOLD else SHIPPING_FEE
    total = subtotal + shipping

    now = datetime.now(timezone.utc).isoformat()
    order_id = f"WW{datetime.now().strftime('%y%m%d%H%M%S')}"

    order = {
        "id": order_id,
        "session_id": payload.session_id,
        "user_id": user_id,          # None for guest orders
        "items": items,
        "customer": payload.customer.model_dump(),
        "paymentMethod": payload.paymentMethod,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "createdAt": now,
        "status": "Confirmed",
    }

    db.insert("orders", order)

    # Clear the cart
    remaining_carts = [c for c in carts if c["session_id"] != payload.session_id]
    db.save("carts", remaining_carts)

    return OrderResponse(**{k: v for k, v in order.items() if k not in ("session_id", "user_id")})


@router.get("/my", response_model=list[OrderResponse])
def list_my_orders(authorization: str = Header(...)):
    """
    Return all orders for the authenticated user (identified by Bearer token).
    Merges orders matched by user_id (new) and by session_id (legacy guest orders
    whose session_id matches the user's stored session).
    """
    token = authorization.removeprefix("Bearer ").strip()
    user = _user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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
    authorization: Optional[str] = Header(default=None),
):
    """
    Return a specific order by its ID.
    If a Bearer token is provided, verifies the order belongs to that user.
    """
    all_orders = db.find_all("orders")
    order = next((o for o in all_orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Auth check when token is supplied
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
        user = _user_from_token(token)
        if user:
            belongs = (
                order.get("user_id") == user["id"]
                or order.get("customer", {}).get("email", "").lower() == user["email"].lower()
            )
            if not belongs:
                raise HTTPException(status_code=403, detail="Access denied")

    return OrderResponse(**{k: v for k, v in order.items() if k not in ("session_id", "user_id")})
