"""
POST /api/orders/place          — place an order (reads cart, clears it, returns order)
GET  /api/orders/{session_id}   — list all orders for a session
GET  /api/orders/detail/{id}    — single order detail
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.schemas.orders import PlaceOrderRequest, OrderResponse
from app import database as db

router = APIRouter(prefix="/api/orders", tags=["Orders"])

SHIPPING_FREE_THRESHOLD = 2000
SHIPPING_FEE = 99


@router.post("/place", response_model=OrderResponse)
def place_order(payload: PlaceOrderRequest):
    """
    Read the session cart, create an order record, clear the cart,
    and return the confirmed order.
    """
    carts = db.find_all("carts")
    cart = next((c for c in carts if c["session_id"] == payload.session_id), None)

    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    if payload.paymentMethod not in ("upi", "card", "cod"):
        raise HTTPException(status_code=400, detail="Invalid payment method")

    items = cart["items"]
    subtotal = sum(it["price"] * it.get("quantity", 1) for it in items)
    shipping = 0 if subtotal >= SHIPPING_FREE_THRESHOLD else SHIPPING_FEE
    total = subtotal + shipping

    now = datetime.now(timezone.utc).isoformat()
    order_id = f"WW{datetime.now().strftime('%y%m%d%H%M%S')}"

    order = {
        "id": order_id,
        "session_id": payload.session_id,
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

    return OrderResponse(**{k: v for k, v in order.items() if k != "session_id"})


@router.get("/{session_id}", response_model=list[OrderResponse])
def list_orders(session_id: str):
    """Return all orders placed in this session."""
    all_orders = db.find_all("orders")
    session_orders = [o for o in all_orders if o.get("session_id") == session_id]
    return [OrderResponse(**{k: v for k, v in o.items() if k != "session_id"}) for o in session_orders]


@router.get("/detail/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    """Return a specific order by its ID."""
    all_orders = db.find_all("orders")
    order = next((o for o in all_orders if o["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(**{k: v for k, v in order.items() if k != "session_id"})
