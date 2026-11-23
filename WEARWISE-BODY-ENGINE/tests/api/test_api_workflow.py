"""
WearWise Phase 6A End-to-End API Integration Test Suite
Verifies the complete mandatory workflow:
  Create Profile -> Generate Avatar -> Save Measurements -> Register Garment -> Evaluate Fit -> Retrieve Fit Report
Also verifies explicit ownership enforcement, optimistic locking, and canonical error envelopes.
"""

import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.api.app import app
from app.storage.local import LocalStorageProvider


@pytest.fixture
def test_db_session(tmp_path):
    """Provides isolated SQLite database and local asset directory for tests."""
    db_file = tmp_path / "test_wearwise.db"
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
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db_session):
    return TestClient(app)


def test_health_and_openapi(client):
    """Verifies healthcheck and OpenAPI JSON specification generation."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["phase"] == "6A"

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    data = openapi.json()
    assert "paths" in data
    assert "/api/v1/profiles" in data["paths"]
    assert "/api/v1/avatar/generate" in data["paths"]
    assert "/api/v1/garments" in data["paths"]
    assert "/api/v1/fit/recommend" in data["paths"]


def test_control_definitions_catalog(client):
    """Verifies semantic control catalog with defaults and safe bounds."""
    res = client.get("/api/v1/controls/definitions")
    assert res.status_code == 200
    controls = res.json()["controls"]
    assert "shoulder_width" in controls
    assert "chest_fullness" in controls
    assert "waist_definition" in controls
    assert controls["chest_fullness"]["default_value"] == 0.50
    assert controls["chest_fullness"]["safe_min"] == 0.10


def test_complete_vertical_workflow(client):
    """
    Executes the complete mandatory vertical slice:
      1. Create Profile (with canonical stature)
      2. Generate 3D Avatar via NAVER Anny
      3. Verify Extracted Anthropometry is persisted
      4. Stream Private Binary GLB
      5. Register Merchant Garment with sizes & provenance
      6. Execute Honest Fit Evaluation
      7. Retrieve Persisted Fit Recommendation
    """
    user_id = str(uuid.uuid4())
    brand_id = str(uuid.uuid4())
    auth_headers = {"X-User-Id": user_id}
    brand_headers = {"X-Brand-Id": brand_id}

    # 1. Create Profile
    prof_res = client.post(
        "/api/v1/profiles",
        headers=auth_headers,
        json={
            "presentation_gender": "masculine",
            "stature_cm": 178.50,
            "reported_weight_kg": 74.00,
            "initial_controls": {
                "shoulder_width": 0.55,
                "chest_fullness": 0.50,
                "belly_fullness": 0.45,
                "waist_definition": 0.60,
            },
        },
    )
    assert prof_res.status_code == 201
    profile_data = prof_res.json()
    profile_id = profile_data["profile_id"]
    assert profile_data["current_revision"] == 1
    assert profile_data["stature_cm"] == 178.50
    assert "stature" in profile_data["active_measurements"]
    assert profile_data["active_measurements"]["stature"]["value_cm"] == 178.50

    # 2. Generate 3D Avatar (uses real NAVER Anny adapter & Anthropometry extraction)
    gen_res = client.post(
        "/api/v1/avatar/generate",
        headers=auth_headers,
        json={"profile_id": profile_id},
    )
    assert gen_res.status_code == 200
    avatar_data = gen_res.json()
    avatar_id = avatar_data["avatar_id"]
    assert avatar_data["format"] == "glb"
    assert avatar_data["size_bytes"] > 100000
    assert len(avatar_data["sha256_checksum"]) == 64
    assert avatar_data["vertex_count"] > 10000
    assert avatar_data["is_valid_manifold"] is True
    assert "chest_circumference" in avatar_data["extracted_measurements"]

    # 3. Verify Active Measurements in Profile reflect extracted values
    meas_res = client.get(f"/api/v1/profiles/{profile_id}/measurements", headers=auth_headers)
    assert meas_res.status_code == 200
    meas_data = meas_res.json()["measurements"]
    assert "chest_circumference" in meas_data
    assert meas_data["chest_circumference"]["acquisition_method"] == "geometry_extracted"
    assert "waist_planar_circumference" in meas_data

    # 4. Stream Private Binary GLB with ETag
    glb_res = client.get(f"/api/v1/avatar/assets/{avatar_id}.glb", headers=auth_headers)
    assert glb_res.status_code == 200
    assert glb_res.headers["content-type"] == "model/gltf-binary"
    assert glb_res.headers["cache-control"] == "private, no-store"
    etag = glb_res.headers.get("etag")
    assert etag is not None

    # Verify conditional 304 Not Modified
    cached_res = client.get(
        f"/api/v1/avatar/assets/{avatar_id}.glb",
        headers={**auth_headers, "If-None-Match": etag},
    )
    assert cached_res.status_code == 304

    # 5. Register Merchant Garment
    garment_res = client.post(
        "/api/v1/garments",
        headers=brand_headers,
        json={
            "sku": "TSH-CREW-6A",
            "title": "Heavyweight Classic Crewneck Tee",
            "category": "t_shirt",
            "fabric_properties": {
                "fibre_composition": {"cotton": 1.0},
                "mechanical_stretch_pct": 0.015,
                "stretch_recovery_pct": 0.90,
                "stretch_direction": "rigid_zero",
            },
        },
    )
    assert garment_res.status_code == 201
    garment_id = garment_res.json()["garment_id"]

    # Add Size Specifications (S, M, L)
    size_specs = [
        {
            "size_label": "S",
            "sort_order": 1,
            "measurements": [
                {
                    "dimension_code": "garment_half_chest_width",
                    "value_cm": 44.00,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "flat_relaxed_tabletop",
                    "provenance": "brand_size_chart",
                },
                {
                    "dimension_code": "garment_shoulder_seam_width",
                    "value_cm": 39.50,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "straight_across_relaxed",
                    "provenance": "brand_size_chart",
                },
            ],
        },
        {
            "size_label": "M",
            "sort_order": 2,
            "measurements": [
                {
                    "dimension_code": "garment_half_chest_width",
                    "value_cm": 46.50,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "flat_relaxed_tabletop",
                    "provenance": "brand_size_chart",
                },
                {
                    "dimension_code": "garment_shoulder_seam_width",
                    "value_cm": 41.50,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "straight_across_relaxed",
                    "provenance": "brand_size_chart",
                },
            ],
        },
        {
            "size_label": "L",
            "sort_order": 3,
            "measurements": [
                {
                    "dimension_code": "garment_half_chest_width",
                    "value_cm": 50.00,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "flat_relaxed_tabletop",
                    "provenance": "brand_size_chart",
                },
                {
                    "dimension_code": "garment_shoulder_seam_width",
                    "value_cm": 44.00,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "straight_across_relaxed",
                    "provenance": "brand_size_chart",
                },
            ],
        },
    ]

    for s in size_specs:
        add_s_res = client.post(
            f"/api/v1/garments/{garment_id}/sizes",
            headers=brand_headers,
            json=s,
        )
        assert add_s_res.status_code == 201

    # 6. Evaluate Honest Fit
    fit_res = client.post(
        "/api/v1/fit/recommend",
        headers=auth_headers,
        json={
            "profile_id": profile_id,
            "garment_id": garment_id,
            "user_fit_preference": "regular",
        },
    )
    assert fit_res.status_code == 200
    fit_data = fit_res.json()
    assert fit_data["recommended_size"] in ("S", "M", "L")
    assert fit_data["status"] == "recommended"
    assert fit_data["composite_fit_score"] > 0.0
    assert len(fit_data["regional_comparisons"]) > 0
    rec_id = fit_data["recommendation_id"]

    # 7. Retrieve Persisted Fit Recommendation
    get_rec_res = client.get(
        f"/api/v1/fit/recommendations/{rec_id}",
        headers=auth_headers,
    )
    assert get_rec_res.status_code == 200
    rec_data = get_rec_res.json()
    assert rec_data["recommendation_id"] == rec_id
    assert rec_data["recommended_size"] == fit_data["recommended_size"]
    assert rec_data["composite_fit_score"] == fit_data["composite_fit_score"]
    assert "provisional" in rec_data["disclaimer"].lower()


def test_explicit_ownership_enforcement(client):
    """
    Verifies that unauthorized users or brands are rejected with 403 Forbidden.
    """
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    brand_a = str(uuid.uuid4())
    brand_b = str(uuid.uuid4())

    # User A creates profile
    prof_res = client.post(
        "/api/v1/profiles",
        headers={"X-User-Id": user_a},
        json={"presentation_gender": "neutral", "stature_cm": 170.00},
    )
    assert prof_res.status_code == 201
    profile_id = prof_res.json()["profile_id"]

    # User B tries to read User A's profile
    forbidden_res = client.get(
        f"/api/v1/profiles/{profile_id}",
        headers={"X-User-Id": user_b},
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "OWNERSHIP_VIOLATION"

    # User B tries to generate avatar for User A's profile
    gen_forbid = client.post(
        "/api/v1/avatar/generate",
        headers={"X-User-Id": user_b},
        json={"profile_id": profile_id},
    )
    assert gen_forbid.status_code == 403

    # Brand A creates garment
    g_res = client.post(
        "/api/v1/garments",
        headers={"X-Brand-Id": brand_a},
        json={
            "sku": "TSH-TEST-OWN",
            "title": "Brand A Shirt",
            "category": "t_shirt",
            "fabric_properties": {
                "fibre_composition": {"cotton": 1.0},
                "mechanical_stretch_pct": 0.01,
                "stretch_recovery_pct": 0.95,
                "stretch_direction": "rigid_zero",
            },
        },
    )
    assert g_res.status_code == 201
    garment_id = g_res.json()["garment_id"]

    # Brand B tries to modify Brand A's garment sizes
    size_forbid = client.post(
        f"/api/v1/garments/{garment_id}/sizes",
        headers={"X-Brand-Id": brand_b},
        json={
            "size_label": "M",
            "measurements": [
                {
                    "dimension_code": "garment_half_chest_width",
                    "value_cm": 50.0,
                    "tolerance_cm": 1.0,
                }
            ],
        },
    )
    assert size_forbid.status_code == 403
    assert size_forbid.json()["error"]["code"] == "BRAND_OWNERSHIP_VIOLATION"


def test_optimistic_locking_concurrency(client):
    """
    Verifies that supplying a stale expected_revision produces 409 Conflict.
    """
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    prof_res = client.post(
        "/api/v1/profiles",
        headers=headers,
        json={"presentation_gender": "feminine", "stature_cm": 165.00},
    )
    assert prof_res.status_code == 201
    profile_id = prof_res.json()["profile_id"]

    # Update measurements with correct expected_revision = 1 -> bumps to revision 2
    rec1 = client.post(
        f"/api/v1/profiles/{profile_id}/measurements",
        headers=headers,
        json={
            "expected_revision": 1,
            "measurements": [
                {
                    "measurement_code": "waist_planar_circumference",
                    "value_cm": 70.00,
                    "unit": "cm",
                }
            ],
        },
    )
    assert rec1.status_code == 200
    assert rec1.json()["new_revision"] == 2

    # Attempt to update again with stale expected_revision = 1 -> should 409
    stale_res = client.post(
        f"/api/v1/profiles/{profile_id}/measurements",
        headers=headers,
        json={
            "expected_revision": 1,
            "measurements": [
                {
                    "measurement_code": "waist_planar_circumference",
                    "value_cm": 72.00,
                    "unit": "cm",
                }
            ],
        },
    )
    assert stale_res.status_code == 409
    assert stale_res.json()["error"]["code"] == "OPTIMISTIC_LOCK_CONFLICT"


def test_anatomical_bounds_validation(client):
    """
    Verifies that out-of-bounds anthropometry produces structured 422 error envelope.
    """
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    # Stature too small (< 100 cm)
    err_res = client.post(
        "/api/v1/profiles",
        headers=headers,
        json={"presentation_gender": "masculine", "stature_cm": 85.00},
    )
    assert err_res.status_code == 422
    err_json = err_res.json()
    assert "error" in err_json
    assert err_json["error"]["status_code"] == 422
