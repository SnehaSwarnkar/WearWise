"""
Phase 13 Admin Portal, Seller Lifecycle & RBAC End-to-End Integration Tests
"""

import os
import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["WEARWISE_DEV_ADMIN_PASSWORD"] = "123456"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.core.security import ensure_auth_seed_and_migration  # noqa: E402

ensure_auth_seed_and_migration(force=True)
SHOPPER_PW = os.getenv("SEED_SHOPPER_PASSWORD", "WearWiseShopper#2026")


def _admin_client() -> TestClient:
    c = TestClient(app)
    res = c.post("/api/auth/admin/login", json={"email": "admin@wearwise.com", "password": "123456"})
    assert res.status_code == 200, res.text
    csrf = res.cookies.get("ww_csrf_token")
    if csrf:
        c.headers.update({"X-CSRF-Token": csrf})
    return c


def test_non_admin_blocked_from_admin_endpoints():
    client = TestClient(app)
    assert client.get("/api/admin/overview").status_code == 401

    res_shop = client.post("/api/auth/login", json={"email": "shopper@wearwise.test", "password": SHOPPER_PW})
    assert res_shop.status_code == 200, res_shop.text
    assert client.get("/api/admin/overview").status_code == 403
    assert client.get("/api/admin/sellers").status_code == 403
    assert client.get("/api/admin/health").status_code == 403


def test_admin_overview_products_orders_customers_health_and_audit():
    admin = _admin_client()

    ov = admin.get("/api/admin/overview")
    assert ov.status_code == 200
    metrics = ov.json()["metrics"]
    assert metrics["is_demo_payments_only"] is True
    assert metrics["actual_captured_revenue"] == 0
    assert metrics["total_products"] >= 9

    assert admin.get("/api/admin/products").status_code == 200
    assert admin.get("/api/admin/customers").status_code == 200
    assert admin.get("/api/admin/orders").status_code == 200
    hl = admin.get("/api/admin/health")
    assert hl.status_code == 200
    assert "commerce_database" in hl.json()
    assert admin.get("/api/admin/audit-logs").status_code == 200


def test_seller_application_rejection_reapply_and_approval_flow():
    anon = TestClient(app)
    email = f"applicant_{uuid.uuid4().hex[:8]}@brand.test"
    apply_res = anon.post(
        "/api/auth/seller/apply",
        json={
            "owner_name": "Aarav Verma",
            "store_name": "Aarav Tailors",
            "email": email,
            "phone": "+91 9811112233",
            "business_type": "Boutique Studio",
            "business_address": "Bengaluru, IN",
            "store_description": "Tailored organic cotton shirts.",
            "password": "BrandPass#2026",
        },
    )
    assert apply_res.status_code == 200, apply_res.text
    assert apply_res.json()["status"] == "pending_approval"

    pending_login = anon.post("/api/auth/seller/login", json={"email": email, "password": "BrandPass#2026"})
    assert pending_login.status_code == 403
    assert "pending approval" in pending_login.json()["detail"].lower()

    admin = _admin_client()
    sellers = admin.get("/api/admin/sellers").json()["sellers"]
    target = next((s for s in sellers if s["email"] == email), None)
    assert target is not None
    assert target["owner_name"] == "Aarav Verma"

    rej = admin.patch(
        f"/api/admin/sellers/{target['id']}",
        json={"status": "rejected", "reason": "Incomplete sizing guide"},
    )
    assert rej.status_code == 200
    assert rej.json()["status"] == "rejected"

    rej_login = anon.post("/api/auth/seller/login", json={"email": email, "password": "BrandPass#2026"})
    assert rej_login.status_code == 403
    assert "not approved" in rej_login.json()["detail"].lower()

    reapply = anon.post(
        "/api/auth/seller/apply",
        json={
            "owner_name": "Aarav Verma",
            "store_name": "Aarav Tailors",
            "email": email,
            "store_description": "Updated with full S/M/L grading charts.",
            "password": "BrandPass#2026",
        },
    )
    assert reapply.status_code == 200
    assert reapply.json()["status"] == "pending_approval"

    app_res = admin.patch(f"/api/admin/sellers/{target['id']}", json={"status": "active"})
    assert app_res.status_code == 200
    assert app_res.json()["seller_approved"] is True

    ok_login = anon.post("/api/auth/seller/login", json={"email": email, "password": "BrandPass#2026"})
    assert ok_login.status_code == 200
    assert ok_login.json()["user"]["role"] == "seller"
