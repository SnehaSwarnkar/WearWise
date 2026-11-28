"""
WearWise Admin Portal API (`/api/admin/...`)
===========================================
Strictly guarded by `require_admin`.
Provides real database-backed metrics, seller application review & approval,
seller suspension/reactivation, product moderation, order management,
customer management, platform health diagnostics, and audit logging.
"""

from __future__ import annotations

import os
import urllib.request
import json as _json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app import database as db
from app.config import MONGODB_BODY_ENGINE_DB
from app.core.security import normalize_user_record, require_admin, sanitize_user_for_client
from app.routers.products import PRODUCTS, get_platform_vton_status, _list_published_products

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"], dependencies=[Depends(require_admin)])


class AdminSellerActionRequest(BaseModel):
    status: str  # active | rejected | suspended | pending
    reason: Optional[str] = None


class AdminCustomerActionRequest(BaseModel):
    status: str  # active | suspended
    reason: Optional[str] = None


class AdminProductModerationRequest(BaseModel):
    moderation_status: str  # active | disabled | removed
    reason: Optional[str] = None


def _be_db():
    if not db.is_mongo_active():
        return None
    client = db.get_client()
    return client[MONGODB_BODY_ENGINE_DB] if client is not None else None


def _record_audit(admin_user: dict[str, Any], action: str, target_type: str, target_id: str, details: dict[str, Any] | None = None) -> None:
    entry = {
        "id": f"aud-{uuid.uuid4().hex[:10]}",
        "action": action,
        "target_type": target_type,
        "target_id": str(target_id),
        "admin_id": str(admin_user.get("id")),
        "admin_email": str(admin_user.get("email")),
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("admin_audit_logs", entry)


def _get_moderation_map() -> dict[str, dict[str, Any]]:
    rows = db.find_all("product_moderation")
    return {str(r.get("identifier")): r for r in rows if r.get("identifier")}


@router.get("/overview")
def admin_overview(admin_user: dict = Depends(require_admin)):
    """Returns actual database-backed platform counts. Explicitly distinguishes simulated orders from payment revenue."""
    users = [normalize_user_record(u) for u in db.find_all("users")]
    customers = [u for u in users if u["role"] == "shopper"]
    sellers = [u for u in users if u["role"] == "seller"]

    pending_sellers = [s for s in sellers if s["status"] == "pending"]
    approved_sellers = [s for s in sellers if s["status"] == "active" and s["seller_approved"]]
    rejected_sellers = [s for s in sellers if s["status"] == "rejected"]
    suspended_sellers = [s for s in sellers if s["status"] == "suspended"]

    mod_map = _get_moderation_map()
    all_products = _collect_all_admin_products(mod_map)
    active_products = [p for p in all_products if p.get("moderation_status", "active") == "active" and p.get("available", True)]

    orders = db.find_all("orders")
    simulated_order_volume = sum(int(o.get("total", 0) or 0) for o in orders)

    return {
        "admin": sanitize_user_for_client(admin_user),
        "metrics": {
            "total_customers": len(customers),
            "active_customers": len([c for c in customers if c["status"] == "active"]),
            "total_sellers": len(sellers),
            "pending_seller_applications": len(pending_sellers),
            "approved_sellers": len(approved_sellers),
            "rejected_sellers": len(rejected_sellers),
            "suspended_sellers": len(suspended_sellers),
            "total_products": len(all_products),
            "active_products": len(active_products),
            "total_orders": len(orders),
            "simulated_order_volume": simulated_order_volume,
            "is_demo_payments_only": True,
            "actual_captured_revenue": 0,
        },
        "recent_pending_sellers": [sanitize_user_for_client(s) for s in pending_sellers[:5]],
        "recent_orders": sorted(orders, key=lambda o: str(o.get("createdAt") or ""), reverse=True)[:5],
    }


@router.get("/sellers")
def list_sellers(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
):
    users = [normalize_user_record(u) for u in db.find_all("users")]
    sellers = [sanitize_user_for_client(u) for u in users if u["role"] == "seller"]
    if status_filter and status_filter != "all":
        sf = status_filter.strip().lower()
        sellers = [s for s in sellers if s["status"] == sf]
    if search and search.strip():
        q = search.strip().lower()
        sellers = [
            s for s in sellers
            if q in (s.get("store_name") or "").lower()
            or q in (s.get("email") or "").lower()
            or q in (s.get("name") or "").lower()
        ]
    sellers.sort(key=lambda s: (0 if s["status"] == "pending" else 1, str(s.get("createdAt") or "")), reverse=False)
    return {"sellers": sellers, "total": len(sellers)}


@router.patch("/sellers/{seller_id}")
def moderate_seller(
    seller_id: str,
    payload: AdminSellerActionRequest,
    admin_user: dict = Depends(require_admin),
):
    target = db.find_one("users", id=seller_id)
    if not target or (target.get("role") or "shopper") != "seller":
        raise HTTPException(status_code=404, detail="Seller account not found")

    new_status = payload.status.strip().lower()
    if new_status not in {"active", "pending", "rejected", "suspended"}:
        raise HTTPException(status_code=400, detail="Invalid seller status")

    now_iso = datetime.now(timezone.utc).isoformat()
    updates: dict[str, Any] = {
        "status": new_status,
        "is_active": new_status == "active",
        "seller_approved": new_status == "active",
        "updatedAt": now_iso,
    }
    if new_status == "active":
        updates["rejection_reason"] = None
        updates["verified_at"] = now_iso
    elif new_status == "rejected":
        updates["rejection_reason"] = (payload.reason or "Application did not meet marketplace verification requirements.").strip()
    elif new_status == "suspended" and payload.reason:
        updates["rejection_reason"] = payload.reason.strip()

    updated = db.update_one("users", {"id": seller_id}, updates)
    _record_audit(
        admin_user,
        action=f"SELLER_{new_status.upper()}",
        target_type="seller",
        target_id=seller_id,
        details={"email": target.get("email"), "store_name": target.get("store_name"), "reason": payload.reason},
    )
    return sanitize_user_for_client(updated or {**target, **updates})


def _collect_all_admin_products(mod_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def _apply_mod(item: dict[str, Any]) -> dict[str, Any]:
        key = str(item.get("sku") or item.get("id"))
        mod = mod_map.get(key) or {}
        return {
            **item,
            "moderation_status": mod.get("moderation_status", "active"),
            "moderation_reason": mod.get("reason"),
        }

    # 1. Published products
    for p in _list_published_products(include_disabled=True):
        key = str(p.get("sku") or p.get("id"))
        seen_keys.add(key)
        items.append(_apply_mod({
            "id": str(p.get("id")),
            "sku": p.get("sku"),
            "name": p.get("name"),
            "category": p.get("category"),
            "gender": p.get("gender", "unisex"),
            "price": p.get("price"),
            "seller_name": p.get("seller_name") or p.get("brand"),
            "status": "published",
            "available": p.get("available", True),
            "inventory_count": p.get("inventory_count", 25),
            "try_on_mode": p.get("try_on_mode", "IMAGE_ONLY"),
            "source": "published_catalog",
        }))

    # 2. Seller drafts / digital_garments
    bedb = _be_db()
    seller_docs = list(bedb["digital_garments"].find({"is_deleted": {"$ne": True}}, {"_id": 0})) if bedb is not None else db.find_all("seller_products")
    for g in seller_docs:
        if g.get("is_deleted"):
            continue
        key = str(g.get("sku") or g.get("id"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        items.append(_apply_mod({
            "id": str(g.get("id")),
            "sku": g.get("sku"),
            "name": g.get("name"),
            "category": g.get("category", "Tops"),
            "gender": g.get("gender", "unisex"),
            "price": g.get("price", 0),
            "seller_name": g.get("seller_name") or "Seller Studio",
            "status": g.get("status", "draft"),
            "available": g.get("available", True),
            "inventory_count": g.get("inventory_count", 25),
            "try_on_mode": g.get("try_on_mode", "IMAGE_ONLY"),
            "source": "seller_catalog",
        }))

    # 3. Baseline platform catalog
    for sp in PRODUCTS:
        key = str(sp.get("sku") or sp.get("id"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        items.append(_apply_mod({
            "id": str(sp.get("id")),
            "sku": sp.get("sku"),
            "name": sp.get("name"),
            "category": sp.get("category"),
            "gender": sp.get("gender", "unisex"),
            "price": sp.get("price"),
            "seller_name": sp.get("seller_name") or sp.get("brand"),
            "status": "published",
            "available": sp.get("available", True),
            "inventory_count": sp.get("inventory_count", 25),
            "try_on_mode": sp.get("try_on_mode", "IMAGE_ONLY"),
            "source": "marketplace_catalog",
        }))

    return items


@router.get("/products")
def list_admin_products(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
):
    mod_map = _get_moderation_map()
    products = _collect_all_admin_products(mod_map)
    if status_filter and status_filter != "all":
        sf = status_filter.strip().lower()
        products = [p for p in products if p.get("moderation_status", "active") == sf or p.get("status") == sf]
    if search and search.strip():
        q = search.strip().lower()
        products = [
            p for p in products
            if q in str(p.get("name") or "").lower()
            or q in str(p.get("sku") or "").lower()
            or q in str(p.get("seller_name") or "").lower()
        ]
    return {"products": products, "total": len(products)}


@router.patch("/products/{identifier}")
def moderate_product(
    identifier: str,
    payload: AdminProductModerationRequest,
    admin_user: dict = Depends(require_admin),
):
    new_mod = payload.moderation_status.strip().lower()
    if new_mod not in {"active", "disabled", "removed"}:
        raise HTTPException(status_code=400, detail="moderation_status must be active, disabled, or removed")

    now_iso = datetime.now(timezone.utc).isoformat()
    existing = db.find_one("product_moderation", identifier=identifier)
    doc = {
        "identifier": identifier,
        "moderation_status": new_mod,
        "reason": (payload.reason or "").strip() or None,
        "updated_at": now_iso,
        "updated_by": admin_user.get("email"),
    }
    if existing:
        db.update_one("product_moderation", {"identifier": identifier}, doc)
    else:
        db.insert("product_moderation", doc)

    # Also propagate to seller/published stores if present
    bedb = _be_db()
    if bedb is not None:
        bedb["digital_garments"].update_many(
            {"$or": [{"sku": identifier}, {"id": identifier}]},
            {"$set": {"available": new_mod == "active", "is_deleted": new_mod == "removed", "updated_at": now_iso}},
        )
    if db.is_mongo_active():
        cdb = db.get_db()
        if cdb is not None:
            cdb["catalog_publications"].update_many(
                {"sku": identifier},
                {"$set": {"moderation_status": new_mod, "available": new_mod == "active"}},
            )

    _record_audit(
        admin_user,
        action=f"PRODUCT_{new_mod.upper()}",
        target_type="product",
        target_id=identifier,
        details={"reason": payload.reason},
    )
    return doc


@router.get("/orders")
def list_admin_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
):
    orders = db.find_all("orders")
    if status_filter and status_filter != "all":
        sf = status_filter.strip().lower()
        orders = [o for o in orders if str(o.get("status") or "").lower() == sf]
    if search and search.strip():
        q = search.strip().lower()
        orders = [
            o for o in orders
            if q in str(o.get("id") or "").lower()
            or q in str((o.get("customer") or {}).get("email") or "").lower()
            or q in str((o.get("customer") or {}).get("firstName") or "").lower()
        ]
    orders.sort(key=lambda o: str(o.get("createdAt") or ""), reverse=True)
    safe_orders = [
        {
            "id": o.get("id"),
            "createdAt": o.get("createdAt"),
            "status": o.get("status", "Confirmed"),
            "subtotal": o.get("subtotal", 0),
            "shipping": o.get("shipping", 0),
            "total": o.get("total", 0),
            "paymentMethod": o.get("paymentMethod"),
            "payment_status": o.get("payment_status", "DEMO_NO_PAYMENT_CAPTURED"),
            "is_demo_checkout": bool(o.get("is_demo_checkout", True)),
            "items_count": len(o.get("items") or []),
            "items": o.get("items") or [],
            "customer_name": f"{(o.get('customer') or {}).get('firstName', '')} {(o.get('customer') or {}).get('lastName', '')}".strip() or "Customer",
            "customer_email": (o.get("customer") or {}).get("email", ""),
            "city": (o.get("customer") or {}).get("city", ""),
        }
        for o in orders
    ]
    return {"orders": safe_orders, "total": len(safe_orders)}


@router.get("/customers")
def list_admin_customers(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
):
    users = [normalize_user_record(u) for u in db.find_all("users")]
    customers = [sanitize_user_for_client(u) for u in users if u["role"] == "shopper"]
    if status_filter and status_filter != "all":
        sf = status_filter.strip().lower()
        customers = [c for c in customers if c["status"] == sf]
    if search and search.strip():
        q = search.strip().lower()
        customers = [
            c for c in customers
            if q in (c.get("name") or "").lower() or q in (c.get("email") or "").lower()
        ]
    customers.sort(key=lambda c: str(c.get("createdAt") or ""), reverse=True)
    return {"customers": customers, "total": len(customers)}


@router.patch("/customers/{customer_id}")
def update_customer_status(
    customer_id: str,
    payload: AdminCustomerActionRequest,
    admin_user: dict = Depends(require_admin),
):
    target = db.find_one("users", id=customer_id)
    if not target or (target.get("role") or "shopper") != "shopper":
        raise HTTPException(status_code=404, detail="Customer account not found")

    new_status = payload.status.strip().lower()
    if new_status not in {"active", "suspended"}:
        raise HTTPException(status_code=400, detail="Status must be active or suspended")

    updated = db.update_one(
        "users",
        {"id": customer_id},
        {"status": new_status, "is_active": new_status == "active"},
    )
    _record_audit(
        admin_user,
        action=f"CUSTOMER_{new_status.upper()}",
        target_type="customer",
        target_id=customer_id,
        details={"email": target.get("email"), "reason": payload.reason},
    )
    return sanitize_user_for_client(updated or target)


@router.get("/health")
def admin_platform_health():
    """Admin-only platform service and connectivity health."""
    commerce_db = db.ping()
    vton_status = get_platform_vton_status()

    body_engine_url = os.getenv("BODY_ENGINE_URL", "http://127.0.0.1:8000").rstrip("/")
    body_engine_status: dict[str, Any] = {"ok": False, "status": "unreachable"}
    try:
        with urllib.request.urlopen(f"{body_engine_url}/health", timeout=0.6) as resp:
            body_engine_status = {"ok": True, **_json.loads(resp.read().decode("utf-8"))}
    except Exception as exc:
        body_engine_status = {"ok": False, "status": "unreachable", "detail": str(exc)[:120]}

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "commerce_api": {"ok": True, "status": "healthy"},
        "commerce_database": {
            "ok": bool(commerce_db.get("ok")),
            "engine": commerce_db.get("engine"),
            "status": commerce_db.get("status"),
        },
        "body_engine": body_engine_status,
        "vton_provider": vton_status,
    }


@router.get("/audit-logs")
def list_audit_logs(limit: int = Query(50, ge=1, le=200)):
    logs = db.find_all("admin_audit_logs")
    logs.sort(key=lambda l: str(l.get("timestamp") or ""), reverse=True)
    return {"logs": logs[:limit], "total": len(logs)}
