import hashlib
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"

COMMERCE_ROOT = Path(__file__).resolve().parents[1]
if str(COMMERCE_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMERCE_ROOT))

from app.main import app
from app import database as db
from app.core.security import ensure_auth_seed_and_migration

ensure_auth_seed_and_migration(force=True)
client = TestClient(app)

SELLER_PW = os.getenv("SEED_SELLER_PASSWORD", "WearWiseSeller#2026")
SHOPPER_PW = os.getenv("SEED_SHOPPER_PASSWORD", "WearWiseShopper#2026")
ADMIN_PW = os.getenv("SEED_ADMIN_PASSWORD", "WearWiseAdmin#2026")


def _signup_shopper(email: str, password: str = "ShopperPass#123"):
    return client.post(
        "/api/auth/signup",
        json={
            "name": "Phase 13 Shopper",
            "email": email,
            "password": password,
            "role": "seller",
            "seller_approved": True,
        },
    )


def test_role_specific_login_and_privilege_escalation_blocked():
    shopper_email = f"p13.shopper.{uuid.uuid4().hex[:6]}@wearwise.test"
    r_reg = _signup_shopper(shopper_email)
    assert r_reg.status_code == 200
    reg_body = r_reg.json()
    # Public signup strictly ignores client-supplied role/seller_approved
    assert reg_body["user"]["role"] == "shopper"
    assert reg_body["user"]["seller_approved"] is False

    # Shopper login succeeds for shopper
    r_sh_ok = client.post("/api/auth/login", json={"email": shopper_email, "password": "ShopperPass#123"})
    assert r_sh_ok.status_code == 200
    assert r_sh_ok.json()["user"]["role"] == "shopper"
    assert "ww_auth_session" in r_sh_ok.cookies
    shopper_token = r_sh_ok.json()["access_token"]

    # Seller login rejects shopper cleanly
    r_sh_on_seller = client.post("/api/auth/seller/login", json={"email": shopper_email, "password": "ShopperPass#123"})
    assert r_sh_on_seller.status_code == 403
    assert "registered as a shopper" in r_sh_on_seller.json()["detail"].lower()

    # Approved seller login succeeds on seller portal
    r_sl_ok = client.post("/api/auth/seller/login", json={"email": "seller@wearwise.studio", "password": SELLER_PW})
    assert r_sl_ok.status_code == 200
    assert r_sl_ok.json()["user"]["role"] == "seller"
    assert r_sl_ok.json()["user"]["seller_approved"] is True
    assert "ww_auth_session" in r_sl_ok.cookies

    # Shopper login rejects seller cleanly
    r_sl_on_shopper = client.post("/api/auth/login", json={"email": "seller@wearwise.studio", "password": SELLER_PW})
    assert r_sl_on_shopper.status_code == 403
    assert "seller account" in r_sl_on_shopper.json()["detail"].lower()

    # Pending seller cannot log in to Seller Portal
    r_pending = client.post("/api/auth/seller/login", json={"email": "pending.seller@wearwise.studio", "password": SELLER_PW})
    assert r_pending.status_code == 403
    assert "pending approval" in r_pending.json()["detail"].lower()

    # Shopper cannot self-promote via profile PATCH
    r_patch = client.patch(
        "/api/auth/profile",
        json={"gender": "women", "role": "seller", "seller_approved": True},
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["role"] == "shopper"
    assert r_patch.json()["seller_approved"] is False


def test_rbac_enforcement_across_seller_shopper_and_admin_endpoints():
    shopper_email = f"p13.rbac.{uuid.uuid4().hex[:6]}@wearwise.test"
    r_reg = _signup_shopper(shopper_email)
    shopper_tok = r_reg.json()["access_token"]
    shopper_hdr = {"Authorization": f"Bearer {shopper_tok}"}

    s1_tok = client.post(
        "/api/auth/seller/login",
        json={"email": "seller@wearwise.studio", "password": SELLER_PW},
    ).json()["access_token"]
    s2_tok = client.post(
        "/api/auth/seller/login",
        json={"email": "studio.two@wearwise.studio", "password": SELLER_PW},
    ).json()["access_token"]
    s1_hdr = {"Authorization": f"Bearer {s1_tok}"}
    s2_hdr = {"Authorization": f"Bearer {s2_tok}"}

    # Unauthenticated requests blocked (fresh anonymous client without session cookie)
    anon = TestClient(app)
    assert anon.get("/api/auth/me").status_code == 401
    assert anon.get("/api/orders/my").status_code == 401
    assert anon.get("/api/seller/dashboard").status_code == 401
    assert anon.get("/api/seller/products").status_code == 401
    assert anon.get("/api/seller/orders").status_code == 401

    # Shopper blocked from all seller & admin endpoints
    assert client.get("/api/seller/dashboard", headers=shopper_hdr).status_code == 403
    assert client.get("/api/seller/products", headers=shopper_hdr).status_code == 403
    assert client.post(
        "/api/seller/products",
        json={"name": "Rogue", "sku": f"ROG-{uuid.uuid4().hex[:6]}", "price": 999},
        headers=shopper_hdr,
    ).status_code == 403
    assert client.get("/api/auth/admin/sellers", headers=shopper_hdr).status_code == 403

    # Seller blocked from shopper-only endpoints (orders/my, wardrobe, saved, avatar, assistant, reviews)
    assert client.get("/api/orders/my", headers=s1_hdr).status_code == 403
    assert client.get("/api/wardrobe/sess-test", headers=s1_hdr).status_code == 403
    assert client.get("/api/saved/looks/sess-test", headers=s1_hdr).status_code == 403
    assert client.get("/api/avatar/sess-test", headers=s1_hdr).status_code == 403
    assert client.post("/api/assistant/chat", json={"session_id": "sess-test", "message": "hi"}, headers=s1_hdr).status_code == 403
    assert client.post(
        "/api/products/sku/TSH-WW-CREW-001/reviews",
        json={"rating": 5, "comment": "Self review attempt"},
        headers=s1_hdr,
    ).status_code == 403

    # Cross-seller isolation: Seller 1 creates product; Seller 2 cannot modify it
    sku = f"P13-OWN-{uuid.uuid4().hex[:6].upper()}"
    r_create = client.post(
        "/api/seller/products",
        json={"name": "Studio One Jacket", "sku": sku, "category": "Jackets", "price": 2599, "try_on_mode": "IMAGE_ONLY"},
        headers=s1_hdr,
    )
    assert r_create.status_code == 201
    prod_id = r_create.json()["id"]

    r_tamper = client.patch(f"/api/seller/products/{prod_id}", json={"price": 1}, headers=s2_hdr)
    assert r_tamper.status_code == 403

    # Order placed on Seller 1's flagship SKU appears for Seller 1 and NOT Seller 2
    sess = f"sess-p13-{uuid.uuid4().hex[:6]}"
    client.post(
        "/api/cart/add",
        json={"session_id": sess, "item": {"id": 1, "name": "Cherry Baby Tee", "price": 799, "quantity": 1, "size": "M", "sku": "TSH-WW-CREW-001"}},
    )
    r_ord = client.post(
        "/api/orders/place",
        json={
            "session_id": sess,
            "customer": {
                "firstName": "Riya",
                "lastName": "Shopper",
                "email": shopper_email,
                "phone": "9876543210",
                "address": "12 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
            },
            "paymentMethod": "upi",
            "idempotency_key": f"idem-{uuid.uuid4().hex[:8]}",
        },
        headers=shopper_hdr,
    )
    assert r_ord.status_code == 200
    oid = r_ord.json()["id"]

    s1_orders = client.get("/api/seller/orders", headers=s1_hdr).json()["orders"]
    s2_orders = client.get("/api/seller/orders", headers=s2_hdr).json()["orders"]
    assert any(o["id"] == oid for o in s1_orders)
    assert all(o["id"] != oid for o in s2_orders)
    assert client.patch(f"/api/seller/orders/{oid}/status", json={"status": "Shipped"}, headers=s2_hdr).status_code == 403


def test_logout_revocation_csrf_and_admin_seller_approval_lifecycle():
    # Login via cookie client & verify CSRF requirement + logout revocation
    c = TestClient(app)
    r_login = c.post("/api/auth/login", json={"email": "shopper@wearwise.test", "password": SHOPPER_PW})
    assert r_login.status_code == 200
    tok = r_login.json()["access_token"]
    csrf = c.cookies.get("ww_csrf_token")
    assert csrf

    # Cookie-based unsafe mutation without X-CSRF-Token rejected (403)
    r_no_csrf = c.patch("/api/auth/profile", json={"gender": "women"})
    assert r_no_csrf.status_code == 403

    # Cookie-based unsafe mutation WITH X-CSRF-Token succeeds (200)
    r_with_csrf = c.patch("/api/auth/profile", json={"gender": "women"}, headers={"X-CSRF-Token": csrf})
    assert r_with_csrf.status_code == 200

    # Logout invalidates session JWT jti even for Bearer reuse
    r_logout = c.post("/api/auth/logout")
    assert r_logout.status_code == 200
    assert c.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401

    # Admin provisions a pending seller, verifies login blocked, then approves & verifies login succeeds
    admin_tok = client.post(
        "/api/auth/admin/login",
        json={"email": "admin@wearwise.studio", "password": ADMIN_PW},
    ).json()["access_token"]
    admin_hdr = {"Authorization": f"Bearer {admin_tok}"}

    new_seller_email = f"approved.{uuid.uuid4().hex[:6]}@wearwise.studio"
    r_prov = client.post(
        "/api/auth/admin/sellers",
        json={
            "name": "New Brand",
            "email": new_seller_email,
            "password": "BrandPass#2026",
            "store_name": "New Brand Studio",
            "approved": False,
        },
        headers=admin_hdr,
    )
    assert r_prov.status_code == 201
    sid = r_prov.json()["id"]

    # Blocked before approval
    assert client.post("/api/auth/seller/login", json={"email": new_seller_email, "password": "BrandPass#2026"}).status_code == 403

    # Admin approves
    r_app = client.patch(f"/api/auth/admin/sellers/{sid}", json={"status": "active", "seller_approved": True}, headers=admin_hdr)
    assert r_app.status_code == 200
    assert client.post("/api/auth/seller/login", json={"email": new_seller_email, "password": "BrandPass#2026"}).status_code == 200

    # Legacy account without explicit role safely resolves to shopper
    legacy_uid = f"usr-leg-{uuid.uuid4().hex[:6]}"
    db.insert("users", {"id": legacy_uid, "name": "Legacy", "email": f"{legacy_uid}@wearwise.test", "password_hash": "x"})
    legacy_tok = hashlib.sha256(f"wearwise-{legacy_uid}".encode()).hexdigest()
    r_leg_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy_tok}"})
    assert r_leg_me.status_code == 200
    assert r_leg_me.json()["role"] == "shopper"
