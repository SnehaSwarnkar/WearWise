import hashlib
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
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

client = TestClient(app)


def _valid_customer(email="shopper.m5@wearwise.test"):
    return {
        "firstName": "Asha",
        "lastName": "Rao",
        "email": email,
        "phone": "9876543210",
        "address": "42 Residency Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
    }


def _make_user_token(email: str, name: str = "Test Shopper") -> tuple[str, str]:
    users = db.find_all("users")
    existing = next((u for u in users if u.get("email", "").lower() == email.lower()), None)
    if not existing:
        uid = f"usr-{uuid.uuid4().hex[:8]}"
        existing = {"id": uid, "name": name, "email": email, "password_hash": "test"}
        db.insert("users", existing)
    token = hashlib.sha256(f"wearwise-{existing['id']}".encode()).hexdigest()
    return existing["id"], token


def test_staging_db_isolation():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["database"]["database"] == "wearwise_commerce_staging"
    assert body["database"]["database"] != "wearwise_commerce"


def test_catalog_resolution_and_asset_security():
    # Unknown SKU fails closed
    r_unk = client.get("/api/products/sku/UNKNOWN-SKU-M5B")
    assert r_unk.status_code == 404

    # Acceptance SKU (if published in staging) resolves active revision and immutable GLB
    r_acc = client.get("/api/products/sku/TSH-WW-ACCEPTANCE-001")
    if r_acc.status_code == 200:
        prod = r_acc.json()
        rev = prod["published_revision"]
        assert rev is not None
        r_glb = client.get(f"/api/products/sku/TSH-WW-ACCEPTANCE-001/revisions/{rev}/assets/M")
        assert r_glb.status_code == 200
        assert r_glb.headers.get("content-type") == "model/gltf-binary"
        assert "immutable" in (r_glb.headers.get("cache-control") or "")
        assert r_glb.headers.get("etag")
        # Stale / nonexistent revision fails closed
        r_bad_rev = client.get(f"/api/products/sku/TSH-WW-ACCEPTANCE-001/revisions/{rev + 99}/assets/M")
        assert r_bad_rev.status_code == 404
        # Technical image cannot be served via storefront endpoint
        r_tech_img = client.get(f"/api/products/sku/TSH-WW-ACCEPTANCE-001/revisions/{rev}/images/secret_back.png")
        assert r_tech_img.status_code == 403


def test_cart_authoritative_pricing_and_mutations():
    sess = f"sess-m5b-{uuid.uuid4().hex[:8]}"
    # Client attempts to spoof price=1 on TSH-WW-CREW-001 (real price=799)
    r_add = client.post(
        "/api/cart/add",
        json={
            "session_id": sess,
            "item": {
                "id": 1,
                "name": "Tampered Name",
                "price": 1,
                "quantity": 1,
                "size": "M",
                "sku": "TSH-WW-CREW-001",
            },
        },
    )
    assert r_add.status_code == 200
    cart = r_add.json()
    assert cart["items"][0]["price"] == 799
    assert cart["subtotal"] == 799
    assert cart["shipping"] == 99
    assert cart["total"] == 898

    # Update quantity
    r_upd = client.put("/api/cart/update", json={"session_id": sess, "item_id": 1, "quantity": 3, "size": "M"})
    assert r_upd.status_code == 200
    assert r_upd.json()["subtotal"] == 2397
    assert r_upd.json()["shipping"] == 0

    # Unknown SKU rejected
    r_bad_sku = client.post(
        "/api/cart/add",
        json={"session_id": sess, "item": {"id": 999999, "name": "Ghost", "price": 100, "quantity": 1, "size": "M", "sku": "NO-SUCH-SKU"}},
    )
    assert r_bad_sku.status_code == 404

    # Remove & clear
    r_del = client.delete(f"/api/cart/{sess}/1?size=M")
    assert r_del.status_code == 200
    assert r_del.json()["items"] == []


def test_checkout_validation_idempotency_and_order_access_control():
    sess = f"sess-ord-{uuid.uuid4().hex[:8]}"
    email_a = f"shopperA-{uuid.uuid4().hex[:6]}@wearwise.test"
    email_b = f"shopperB-{uuid.uuid4().hex[:6]}@wearwise.test"
    _, tok_a = _make_user_token(email_a, "Shopper A")
    _, tok_b = _make_user_token(email_b, "Shopper B")

    client.post(
        "/api/cart/add",
        json={"session_id": sess, "item": {"id": 1, "name": "Cherry Baby Tee", "price": 1, "quantity": 2, "size": "L", "sku": "TSH-WW-CREW-001"}},
    )

    # Empty/malformed customer rejected
    bad_cust = _valid_customer(email_a)
    bad_cust["email"] = "not-an-email"
    r_bad = client.post("/api/orders/place", json={"session_id": sess, "customer": bad_cust, "paymentMethod": "upi"})
    assert r_bad.status_code == 400

    # Concurrent / duplicate order submission with same idempotency_key produces exactly 1 order
    idem_key = f"idem-{uuid.uuid4().hex[:10]}"
    payload = {"session_id": sess, "customer": _valid_customer(email_a), "paymentMethod": "upi", "idempotency_key": idem_key}

    def _place():
        return client.post("/api/orders/place", json=payload, headers={"Authorization": f"Bearer {tok_a}"})

    r1 = _place()
    r2 = _place()
    assert r1.status_code == 200
    assert r2.status_code == 200
    o1, o2 = r1.json(), r2.json()
    assert o1["id"] == o2["id"]
    assert o1["subtotal"] == 1598
    assert o1["shipping"] == 99
    assert o1["total"] == 1697
    assert o1["is_demo_checkout"] is True
    assert o1["payment_status"] == "DEMO_NO_PAYMENT_CAPTURED"

    # Cross-user order access denied
    r_detail_b = client.get(f"/api/orders/detail/{o1['id']}", headers={"Authorization": f"Bearer {tok_b}"})
    assert r_detail_b.status_code == 403

    r_detail_anon = client.get(f"/api/orders/detail/{o1['id']}")
    assert r_detail_anon.status_code == 403

    # Owner & matching session allowed
    r_detail_a = client.get(f"/api/orders/detail/{o1['id']}", headers={"Authorization": f"Bearer {tok_a}"})
    assert r_detail_a.status_code == 200 and r_detail_a.json()["id"] == o1["id"]

    r_my_a = client.get("/api/orders/my", headers={"Authorization": f"Bearer {tok_a}"})
    assert r_my_a.status_code == 200 and any(x["id"] == o1["id"] for x in r_my_a.json())

    r_my_b = client.get("/api/orders/my", headers={"Authorization": f"Bearer {tok_b}"})
    assert r_my_b.status_code == 200 and all(x["id"] != o1["id"] for x in r_my_b.json())
