"""
WearWise Authentication & Identity Security Test Suite
Verifies all 6 required authentication and ownership criteria from Phase 6A review:
  1. Missing credentials in production mode return 401.
  2. Forged identity headers (X-User-Id/X-Brand-Id) cannot impersonate another user in production mode.
  3. Invalid and expired tokens return 401.
  4. A valid User A token cannot access User B's profile (403 Forbidden).
  5. A valid Brand A token cannot modify Brand B's garments (403 Forbidden).
  6. Development authentication is unavailable in production mode.
  7. OpenAPI correctly declares Bearer security scheme.
"""

import uuid
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.api.app import app
from app.api.auth import create_token
import app.config as config
import app.api.auth as auth_module


@pytest.fixture
def auth_test_client(tmp_path):
    """Provides isolated database session for security tests."""
    db_file = tmp_path / "test_auth_security.db"
    test_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Test 1 & 6: Production Mode Rejection of Missing Credentials & Dev Auth
# -----------------------------------------------------------------------------

def test_missing_credentials_in_production_returns_401(auth_test_client, monkeypatch):
    """Proves that missing credentials in production mode return 401 Unauthorized."""
    monkeypatch.setattr(config, "IS_PRODUCTION", True)
    monkeypatch.setattr(config, "ALLOW_DEV_AUTH", False)
    monkeypatch.setattr(auth_module, "IS_PRODUCTION", True)
    monkeypatch.setattr(auth_module, "ALLOW_DEV_AUTH", False)

    res = auth_test_client.get("/api/v1/profiles/c1f7a28e-8e3b-48d9-a791-03f4439c1b3e")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "CREDENTIALS_MISSING"
    assert "Bearer" in res.headers.get("www-authenticate", "")


def test_development_authentication_unavailable_in_production(auth_test_client, monkeypatch):
    """Proves that development fallback identities are strictly unavailable in production mode."""
    monkeypatch.setattr(config, "IS_PRODUCTION", True)
    monkeypatch.setattr(config, "ALLOW_DEV_AUTH", False)
    monkeypatch.setattr(auth_module, "IS_PRODUCTION", True)
    monkeypatch.setattr(auth_module, "ALLOW_DEV_AUTH", False)

    # Calling POST /profiles without token in production mode must fail with 401, not create a dev profile
    res = auth_test_client.post(
        "/api/v1/profiles",
        json={"presentation_gender": "masculine", "stature_cm": 175.0},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "CREDENTIALS_MISSING"


# -----------------------------------------------------------------------------
# Test 2: Forged Identity Headers Ignored in Production
# -----------------------------------------------------------------------------

def test_forged_identity_headers_cannot_impersonate_in_production(auth_test_client, monkeypatch):
    """Proves that forged X-User-Id / X-Brand-Id headers cannot impersonate another user in production mode."""
    monkeypatch.setattr(config, "IS_PRODUCTION", True)
    monkeypatch.setattr(config, "ALLOW_DEV_AUTH", False)
    monkeypatch.setattr(auth_module, "IS_PRODUCTION", True)
    monkeypatch.setattr(auth_module, "ALLOW_DEV_AUTH", False)

    fake_victim_user_id = str(uuid.uuid4())
    res = auth_test_client.get(
        f"/api/v1/profiles/{fake_victim_user_id}",
        headers={"X-User-Id": fake_victim_user_id},
    )
    # Must reject with 401 because X-User-Id is not accepted in production
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "CREDENTIALS_MISSING"


# -----------------------------------------------------------------------------
# Test 3: Invalid and Expired Tokens Return 401
# -----------------------------------------------------------------------------

def test_invalid_tokens_return_401(auth_test_client):
    """Proves that invalid or malformed tokens return 401."""
    # Malformed token string
    res = auth_test_client.get(
        "/api/v1/profiles/c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
        headers={"Authorization": "Bearer invalid.malformed.jwt.token"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"

    # Token with wrong signature
    tampered_token = create_token(uuid.uuid4(), secret_key="wrong-signing-secret-key-32-bytes!")
    res_tampered = auth_test_client.get(
        "/api/v1/profiles/c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res_tampered.status_code == 401
    assert res_tampered.json()["error"]["code"] == "INVALID_TOKEN"


def test_expired_token_returns_401(auth_test_client):
    """Proves that an expired token returns 401 with code TOKEN_EXPIRED."""
    # Mint token that expired 10 minutes ago
    expired_token = create_token(uuid.uuid4(), expires_in_minutes=-10)
    res = auth_test_client.get(
        "/api/v1/profiles/c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "TOKEN_EXPIRED"


# -----------------------------------------------------------------------------
# Test 4: Object-Level Ownership — User A Token Cannot Access User B Profile
# -----------------------------------------------------------------------------

def test_user_a_cannot_access_user_b_profile(auth_test_client):
    """Proves that a valid User A token cannot access User B's profile (403 Forbidden)."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    token_a = create_token(user_a, principal_type="user")
    token_b = create_token(user_b, principal_type="user")

    # User A creates their profile
    create_res = auth_test_client.post(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"presentation_gender": "masculine", "stature_cm": 180.0},
    )
    assert create_res.status_code == 201
    profile_a_id = create_res.json()["profile_id"]

    # User B tries to read User A's profile
    read_res = auth_test_client.get(
        f"/api/v1/profiles/{profile_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert read_res.status_code == 403
    assert read_res.json()["error"]["code"] == "OWNERSHIP_VIOLATION"


# -----------------------------------------------------------------------------
# Test 5: Object-Level Ownership — Brand A Token Cannot Modify Brand B Garment
# -----------------------------------------------------------------------------

def test_brand_a_cannot_modify_brand_b_garment(auth_test_client):
    """Proves that a valid Brand A token cannot modify Brand B's garment (403 Forbidden)."""
    brand_a = uuid.uuid4()
    brand_b = uuid.uuid4()
    token_brand_a = create_token(brand_a, principal_type="brand")
    token_brand_b = create_token(brand_b, principal_type="brand")

    # Brand A creates garment
    g_res = auth_test_client.post(
        "/api/v1/garments",
        headers={"Authorization": f"Bearer {token_brand_a}"},
        json={
            "sku": "TSH-BRAND-A",
            "title": "Brand A Tee",
            "category": "t_shirt",
            "fabric_properties": {
                "fibre_composition": {"cotton": 1.0},
                "mechanical_stretch_pct": 0.015,
                "stretch_recovery_pct": 0.90,
                "stretch_direction": "rigid_zero",
            },
        },
    )
    assert g_res.status_code == 201
    garment_id = g_res.json()["garment_id"]

    # Brand B tries to add size specification to Brand A's garment
    size_res = auth_test_client.post(
        f"/api/v1/garments/{garment_id}/sizes",
        headers={"Authorization": f"Bearer {token_brand_b}"},
        json={
            "size_label": "M",
            "sort_order": 1,
            "measurements": [
                {
                    "dimension_code": "garment_half_chest_width",
                    "value_cm": 48.0,
                    "tolerance_cm": 1.0,
                }
            ],
        },
    )
    assert size_res.status_code == 403
    assert size_res.json()["error"]["code"] == "BRAND_OWNERSHIP_VIOLATION"


# -----------------------------------------------------------------------------
# Test 7: OpenAPI Declares Bearer Security Scheme
# -----------------------------------------------------------------------------

def test_openapi_declares_bearer_security_scheme(auth_test_client):
    """Proves that OpenAPI specification declares the Bearer security scheme."""
    res = auth_test_client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "BearerAuth" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["BearerAuth"]["type"] == "http"
    assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
    assert schema["components"]["securitySchemes"]["BearerAuth"]["bearerFormat"] == "JWT"
