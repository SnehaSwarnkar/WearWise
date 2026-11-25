import os
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"

BODY_ROOT = Path(__file__).resolve().parents[2]
if str(BODY_ROOT) not in sys.path:
    sys.path.insert(0, str(BODY_ROOT))

from app.api.app import app as body_app
from app.api.auth import create_token
from app.db import mongo

body_client = TestClient(body_app)


def test_unauthenticated_and_shopper_cannot_call_merchant_garments_apis():
    # 1. Anonymous request to private merchant list fails closed (401)
    r_anon = body_client.get("/api/v1/merchant/garments")
    assert r_anon.status_code == 401

    # 2. Shopper JWT rejected cleanly on all seller merchant APIs (403)
    shopper_jwt = create_token(uuid.uuid4(), principal_type="shopper")
    hdr = {"Authorization": f"Bearer {shopper_jwt}"}
    assert body_client.get("/api/v1/merchant/garments", headers=hdr).status_code == 403
    assert body_client.post(
        "/api/v1/merchant/garments",
        json={"name": "Bypass", "sku": f"BYP-{uuid.uuid4().hex[:6]}", "price": 1200},
        headers=hdr,
    ).status_code == 403
    assert body_client.post(
        "/api/v1/merchant/garments/ww-seed-tsh-ww-crew-001/publish",
        json={"publisher_id": "shopper"},
        headers=hdr,
    ).status_code == 403


def test_cross_service_cookie_session_csrf_and_revocation():
    jti = uuid.uuid4().hex
    csrf = "csrf-" + uuid.uuid4().hex
    brand_uuid = uuid.UUID("e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e")
    tok = create_token(
        brand_uuid,
        principal_type="brand",
        extra_claims={"jti": jti, "role": "seller", "commerce_user_id": "slr-official-001"},
    )
    sess_col = mongo.get_commerce_collection("auth_sessions")
    if sess_col is not None:
        sess_col.update_one(
            {"jti": jti},
            {"$set": {"jti": jti, "user_id": "slr-official-001", "role": "seller", "revoked": False}},
            upsert=True,
        )

    c = TestClient(body_app)
    c.cookies.set("ww_auth_session", tok)
    c.cookies.set("ww_csrf_token", csrf)

    # Cookie GET works cleanly for seller
    r_get = c.get("/api/v1/merchant/garments")
    assert r_get.status_code == 200

    # Cookie POST without CSRF header fails closed (403)
    r_no_csrf = c.post(
        "/api/v1/merchant/garments",
        json={"name": "No CSRF", "sku": f"NOC-{uuid.uuid4().hex[:6]}", "price": 999},
    )
    assert r_no_csrf.status_code == 403

    # Revoked session rejected across Body Engine (401) when MongoDB session store active
    if sess_col is not None:
        sess_col.update_one({"jti": jti}, {"$set": {"revoked": True}})
        r_revoked = c.get("/api/v1/merchant/garments")
        assert r_revoked.status_code == 401
