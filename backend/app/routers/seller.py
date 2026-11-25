"""
WearWise Seller Portal API (`/api/seller/...`)
==============================================
Strictly requires an authenticated, approved, active `seller` account via `require_active_seller`.
Every operation is scoped strictly to `seller["brand_id"]` — sellers can never view or mutate
another seller's products, inventory, store profile, or customer orders.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app import database as db
from app.config import MONGODB_BODY_ENGINE_DB
from app.core.security import CANONICAL_DEFAULT_BRAND_ID, require_active_seller, sanitize_user_for_client
from app.routers.products import PRODUCTS, VALID_TRY_ON_MODES, build_try_on_capabilities

router = APIRouter(prefix="/api/seller", tags=["Seller Portal"])


class SellerProductCreate(BaseModel):
    name: str
    sku: str
    category: str = "Tops"
    subcategory: str = "Apparel"
    description: str = ""
    color_variant: str = "#151515"
    color_variants: Optional[list[str]] = None
    price: float = Field(..., gt=0)
    currency: str = "INR"
    available_sizes: list[str] = Field(default_factory=lambda: ["S", "M", "L"])
    try_on_mode: str = "IMAGE_ONLY"
    inventory_count: int = Field(25, ge=0)
    available: bool = True


class SellerProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    color_variant: Optional[str] = None
    color_variants: Optional[list[str]] = None
    price: Optional[float] = Field(default=None, gt=0)
    available_sizes: Optional[list[str]] = None
    try_on_mode: Optional[str] = None
    inventory_count: Optional[int] = Field(default=None, ge=0)
    available: Optional[bool] = None


class SellerOrderStatusUpdate(BaseModel):
    status: str  # Confirmed | Packed | Shipped | Delivered | Cancelled


class SellerProfileUpdate(BaseModel):
    name: Optional[str] = None
    store_name: Optional[str] = None
    business_email: Optional[str] = None
    store_description: Optional[str] = None
    brand_tagline: Optional[str] = None


def _be_db():
    if not db.is_mongo_active():
        return None
    client = db.get_client()
    return client[MONGODB_BODY_ENGINE_DB] if client is not None else None


def _commerce_db():
    return db.get_db() if db.is_mongo_active() else None


def _list_seller_garments(brand_id: str) -> list[dict[str, Any]]:
    """Lists garments owned strictly by `brand_id` across Body Engine DB or JSON fallback."""
    bedb = _be_db()
    if bedb is not None:
        docs = list(bedb["digital_garments"].find({"brand_id": brand_id, "is_deleted": {"$ne": True}}, {"_id": 0}))
        return docs
    return [g for g in db.find_all("seller_products") if g.get("brand_id") == brand_id and not g.get("is_deleted")]


def _find_garment_any_owner(identifier: str) -> Optional[dict[str, Any]]:
    bedb = _be_db()
    if bedb is not None:
        doc = bedb["digital_garments"].find_one({"id": identifier, "is_deleted": {"$ne": True}}, {"_id": 0})
        if not doc:
            doc = bedb["digital_garments"].find_one({"sku": identifier, "is_deleted": {"$ne": True}}, {"_id": 0})
        if doc:
            return doc
    for g in db.find_all("seller_products"):
        if not g.get("is_deleted") and (g.get("id") == identifier or g.get("sku") == identifier):
            return g
    return None


def _format_seller_product(doc: dict[str, Any]) -> dict[str, Any]:
    size_variants = doc.get("size_variants") or {}
    mesh_assets = doc.get("mesh_assets") or {}
    has_3d = bool(size_variants) or any(sz in mesh_assets for sz in ("S", "M", "L"))
    images_meta = doc.get("images_meta") or []
    has_photos = bool(images_meta) or any(
        isinstance(im, str) and im for k, im in (doc.get("images") or {}).items() if k in ("front", "back", "left_side")
    )
    caps = build_try_on_capabilities(doc.get("try_on_mode"), has_3d_assets=has_3d, has_photos=has_photos)
    colors = doc.get("color_variants") or ([doc["color_variant"]] if doc.get("color_variant") else ["#151515"])
    return {
        "id": doc.get("id"),
        "sku": doc.get("sku"),
        "brand_id": doc.get("brand_id"),
        "name": doc.get("name"),
        "category": doc.get("category", "Tops"),
        "subcategory": doc.get("subcategory", ""),
        "description": doc.get("description", ""),
        "color_variant": doc.get("color_variant", ""),
        "colors": colors,
        "price": doc.get("price", 0),
        "currency": doc.get("currency", "INR"),
        "available_sizes": doc.get("available_sizes", ["S", "M", "L"]),
        "status": doc.get("status", "draft"),
        "published_revision": doc.get("published_revision"),
        "published_version": doc.get("published_version"),
        "downstream_stale": bool(doc.get("downstream_stale", False)),
        "try_on_mode": caps["mode"],
        "tryOnCapabilities": caps,
        "inventory_count": int(doc.get("inventory_count", 25)),
        "available": bool(doc.get("available", True)),
        "images": doc.get("images", {}),
        "updated_at": doc.get("updated_at") or doc.get("created_at"),
        "created_at": doc.get("created_at"),
    }


def _seller_skus_map(brand_id: str) -> set[str]:
    skus = {g.get("sku") for g in _list_seller_garments(brand_id) if g.get("sku")}
    cdb = _commerce_db()
    if cdb is not None:
        for pub in cdb["catalog_publications"].find({"brand_id": brand_id}, {"_id": 0, "sku": 1}):
            if pub.get("sku"):
                skus.add(pub["sku"])
    if brand_id == CANONICAL_DEFAULT_BRAND_ID:
        for sp in PRODUCTS:
            if sp.get("sku"):
                skus.add(sp["sku"])
    return skus


def _extract_seller_orders(seller: dict[str, Any]) -> list[dict[str, Any]]:
    brand_id = str(seller["brand_id"])
    owned_skus = _seller_skus_map(brand_id)
    seller_orders: list[dict[str, Any]] = []

    for order in db.find_all("orders"):
        matched_items = []
        for item in order.get("items", []):
            item_brand = item.get("seller_brand_id")
            item_sku = item.get("sku")
            if item_brand == brand_id or (not item_brand and item_sku in owned_skus):
                matched_items.append(item)
        if not matched_items:
            continue

        customer = order.get("customer") or {}
        seller_subtotal = sum(int(it.get("price", 0)) * int(it.get("quantity", 1)) for it in matched_items)
        seller_orders.append(
            {
                "id": order["id"],
                "createdAt": order.get("createdAt"),
                "status": order.get("status", "Confirmed"),
                "paymentMethod": order.get("paymentMethod", "upi"),
                "payment_status": order.get("payment_status", "DEMO_NO_PAYMENT_CAPTURED"),
                "items": matched_items,
                "seller_subtotal": seller_subtotal,
                "customer_name": f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() or "Shopper",
                "shipping_city": customer.get("city", ""),
                "shipping_state": customer.get("state", ""),
            }
        )

    seller_orders.sort(key=lambda o: o.get("createdAt", ""), reverse=True)
    return seller_orders


@router.get("/dashboard")
def get_seller_dashboard(seller: dict = Depends(require_active_seller)):
    """Returns factual seller dashboard summary backed strictly by persisted database records."""
    brand_id = str(seller["brand_id"])
    products = [_format_seller_product(d) for d in _list_seller_garments(brand_id)]
    published = [p for p in products if p["status"] == "published"]
    drafts = [p for p in products if p["status"] != "published"]
    attention = [
        p for p in products
        if p["status"] != "published" or p["downstream_stale"] or not p["available"] or p["inventory_count"] <= 0
    ]
    orders = _extract_seller_orders(seller)

    recent_activity = []
    for p in sorted(products, key=lambda x: str(x.get("updated_at") or ""), reverse=True)[:5]:
        recent_activity.append(
            {
                "type": "product",
                "title": f"{p['name']} ({p['sku']})",
                "status": p["status"],
                "timestamp": p.get("updated_at") or p.get("created_at"),
            }
        )
    for o in orders[:5]:
        recent_activity.append(
            {
                "type": "order",
                "title": f"Order {o['id']} · {len(o['items'])} item(s)",
                "status": o["status"],
                "timestamp": o.get("createdAt"),
            }
        )
    recent_activity.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)

    return {
        "seller": sanitize_user_for_client(seller),
        "metrics": {
            "total_products": len(products),
            "published_products": len(published),
            "draft_products": len(drafts),
            "needs_attention": len(attention),
            "orders_count": len(orders),
        },
        "attention_products": attention[:6],
        "recent_activity": recent_activity[:8],
    }


@router.get("/products")
def list_seller_products(seller: dict = Depends(require_active_seller)):
    """Lists all products owned by the authenticated seller."""
    docs = _list_seller_garments(str(seller["brand_id"]))
    items = [_format_seller_product(d) for d in docs]
    items.sort(key=lambda x: str(x.get("updated_at") or ""), reverse=True)
    return {"brand_id": seller["brand_id"], "products": items}


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_seller_product(payload: SellerProductCreate, seller: dict = Depends(require_active_seller)):
    """Creates a new product draft strictly owned by the authenticated seller."""
    sku_clean = payload.sku.strip().upper()
    if len(sku_clean) < 3:
        raise HTTPException(status_code=400, detail="SKU must be at least 3 characters")
    mode = payload.try_on_mode.strip().upper()
    if mode not in VALID_TRY_ON_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid try_on_mode '{mode}'")

    existing = _find_garment_any_owner(sku_clean)
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{sku_clean}' is already in use")

    brand_id = str(seller["brand_id"])
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "brand_id": brand_id,
        "seller_name": seller.get("store_name") or seller.get("name"),
        "name": payload.name.strip(),
        "sku": sku_clean,
        "category": payload.category.strip() or "Tops",
        "subcategory": payload.subcategory.strip() or "Apparel",
        "description": payload.description.strip(),
        "color_variant": payload.color_variant.strip(),
        "color_variants": payload.color_variants or [payload.color_variant.strip()],
        "price": float(payload.price),
        "currency": payload.currency,
        "available_sizes": payload.available_sizes or ["S", "M", "L"],
        "try_on_mode": mode,
        "status": "draft",
        "step_completed": 1,
        "revision": 0,
        "active_revision": None,
        "downstream_stale": False,
        "inventory_count": int(payload.inventory_count),
        "available": bool(payload.available),
        "images": {"front": None, "back": None, "left_side": None, "right_side": None, "close_up": None},
        "images_meta": [],
        "mesh_assets": {},
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
    }

    bedb = _be_db()
    if bedb is not None:
        bedb["digital_garments"].update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
    else:
        db.insert("seller_products", doc)
    return _format_seller_product(doc)


@router.patch("/products/{product_id}")
def update_seller_product(
    product_id: str,
    payload: SellerProductUpdate,
    seller: dict = Depends(require_active_seller),
):
    """Updates an owned seller product's price, colours, sizes, availability, inventory, or try-on mode."""
    target = _find_garment_any_owner(product_id)
    if not target:
        raise HTTPException(status_code=404, detail="Product not found")
    if str(target.get("brand_id")) != str(seller["brand_id"]):
        raise HTTPException(status_code=403, detail="Access denied: you do not own this product.")

    updates: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    data = payload.model_dump(exclude_none=True)
    if "try_on_mode" in data:
        mode = data["try_on_mode"].strip().upper()
        if mode not in VALID_TRY_ON_MODES:
            raise HTTPException(status_code=400, detail=f"Invalid try_on_mode '{mode}'")
        updates["try_on_mode"] = mode
        del data["try_on_mode"]
    updates.update(data)

    bedb = _be_db()
    if bedb is not None:
        bedb["digital_garments"].update_one({"id": target["id"]}, {"$set": updates})
        updated = bedb["digital_garments"].find_one({"id": target["id"]}, {"_id": 0})
        cdb = _commerce_db()
        if cdb is not None and updated and updated.get("status") == "published":
            pub_updates = {
                k: updates[k]
                for k in ("name", "category", "description", "color_variant", "price", "available_sizes", "try_on_mode", "available", "inventory_count", "updated_at")
                if k in updates
            }
            if pub_updates:
                cdb["catalog_publications"].update_one({"sku": updated["sku"]}, {"$set": pub_updates})
    else:
        updated = db.update_one("seller_products", {"id": target["id"]}, updates)

    return _format_seller_product(updated or {**target, **updates})


@router.get("/orders")
def list_seller_orders(seller: dict = Depends(require_active_seller)):
    """Returns only orders containing products belonging to the authenticated seller."""
    return {"brand_id": seller["brand_id"], "orders": _extract_seller_orders(seller)}


@router.patch("/orders/{order_id}/status")
def update_seller_order_status(
    order_id: str,
    payload: SellerOrderStatusUpdate,
    seller: dict = Depends(require_active_seller),
):
    """Updates status for an order containing items owned by the authenticated seller."""
    allowed_statuses = {"Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(allowed_statuses)}")

    order = db.find_one("orders", id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    seller_orders = _extract_seller_orders(seller)
    if not any(o["id"] == order_id for o in seller_orders):
        raise HTTPException(status_code=403, detail="Access denied: order does not belong to your store.")

    updated = db.update_one("orders", {"id": order_id}, {"status": payload.status})
    return {"id": order_id, "status": (updated or order).get("status", payload.status)}


@router.get("/profile")
def get_seller_profile(seller: dict = Depends(require_active_seller)):
    """Returns the authenticated seller's store & business profile."""
    return sanitize_user_for_client(seller)


@router.patch("/profile")
def update_seller_profile(
    payload: SellerProfileUpdate,
    seller: dict = Depends(require_active_seller),
):
    """Updates supported seller store details (never alters role, status, approval, or brand_id)."""
    updates = {
        k: v.strip()
        for k, v in payload.model_dump(exclude_none=True).items()
        if isinstance(v, str)
    }
    if not updates:
        return sanitize_user_for_client(seller)
    updated = db.update_one("users", {"id": seller["id"]}, updates) or seller
    return sanitize_user_for_client(updated)
