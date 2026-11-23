"""
WearWise Phase 6A End-to-End Backend Demonstration Script
Executes the mandatory vertical workflow through the FastAPI application:
  Create Profile -> Generate Avatar -> Save Measurements -> Register Garment -> Evaluate Fit -> Retrieve Fit Report

Generates demonstration artifacts in artifacts/phase6a/:
  - phase6a_e2e_demo_report.json
  - openapi.json
"""

import os
import sys
import json
import time
import uuid
from decimal import Decimal
from pathlib import Path

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db, init_db, set_sqlite_pragma
from app.api.app import app


def run_e2e_demonstration():
    print("=" * 80)
    print("  WearWise — Phase 6A Working Backend Vertical Slice Demonstration")
    print("  Architecture: Modular Monolith | FastAPI | SQLAlchemy | NAVER Anny v0.6.2")
    print("=" * 80)

    # 1. Setup persistent demo SQLite DB
    demo_dir = REPO_ROOT / "data"
    demo_dir.mkdir(parents=True, exist_ok=True)
    demo_db_path = demo_dir / "wearwise_demo.db"
    if demo_db_path.exists():
        demo_db_path.unlink()

    demo_engine = create_engine(
        f"sqlite:///{demo_db_path}",
        connect_args={"check_same_thread": False},
    )
    init_db(demo_engine)
    DemoSession = sessionmaker(autocommit=False, autoflush=False, bind=demo_engine)

    def override_db():
        db = DemoSession()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)

    # 2. Output directory
    artifacts_dir = REPO_ROOT / "artifacts" / "phase6a"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Save OpenAPI spec
    openapi_res = client.get("/openapi.json")
    if openapi_res.status_code == 200:
        (artifacts_dir / "openapi.json").write_text(json.dumps(openapi_res.json(), indent=2), encoding="utf-8")
        print("[OK] Exported OpenAPI specification to artifacts/phase6a/openapi.json")

    # Principals
    demo_user_id = str(uuid.uuid4())
    demo_brand_id = str(uuid.uuid4())
    user_headers = {"X-User-Id": demo_user_id}
    brand_headers = {"X-Brand-Id": demo_brand_id}

    timeline = {}

    # -------------------------------------------------------------------------
    # STEP 1: Create Profile
    # -------------------------------------------------------------------------
    print("\n[Step 1/6] Creating Shopper Body Profile...")
    t0 = time.perf_counter()
    prof_payload = {
        "presentation_gender": "masculine",
        "stature_cm": 178.50,
        "reported_weight_kg": 74.00,
        "initial_controls": {
            "shoulder_width": 0.55,
            "chest_fullness": 0.50,
            "belly_fullness": 0.45,
            "waist_definition": 0.60,
            "arm_fullness": 0.50,
            "hip_fullness": 0.50,
            "thigh_fullness": 0.50,
            "calf_fullness": 0.50,
        },
    }
    r1 = client.post("/api/v1/profiles", headers=user_headers, json=prof_payload)
    assert r1.status_code == 201, f"Failed to create profile: {r1.text}"
    profile_data = r1.json()
    profile_id = profile_data["profile_id"]
    timeline["step_1_create_profile_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    print(f"  -> Profile ID: {profile_id}")
    print(f"  -> Stature: {profile_data['stature_cm']} cm (Canonical initial measurement created)")
    print(f"  -> Revision: {profile_data['current_revision']}")
    print(f"  -> Duration: {timeline['step_1_create_profile_ms']} ms")

    # -------------------------------------------------------------------------
    # STEP 2: Generate 3D Avatar (Real NAVER Anny + Extraction)
    # -------------------------------------------------------------------------
    print("\n[Step 2/6] Orchestrating Real 3D Avatar Generation (NAVER Anny v0.6.2)...")
    t0 = time.perf_counter()
    r2 = client.post("/api/v1/avatar/generate", headers=user_headers, json={"profile_id": profile_id})
    assert r2.status_code == 200, f"Failed to generate avatar: {r2.text}"
    avatar_data = r2.json()
    avatar_id = avatar_data["avatar_id"]
    timeline["step_2_generate_avatar_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    print(f"  -> Avatar Asset ID: {avatar_id}")
    print(f"  -> Format: {avatar_data['format'].upper()} | Size: {avatar_data['size_bytes']} bytes")
    print(f"  -> Vertices: {avatar_data['vertex_count']:,} | Manifold: {avatar_data['is_valid_manifold']}")
    print(f"  -> SHA-256 Digest: {avatar_data['sha256_checksum']}")
    print(f"  -> Mesh Engine Generation: {avatar_data['generation_duration_ms']} ms")
    print(f"  -> Total Step 2 (Mesh + Slicing + Storage): {timeline['step_2_generate_avatar_ms']} ms")

    # -------------------------------------------------------------------------
    # STEP 3: Verify Saved Measurements in Profile
    # -------------------------------------------------------------------------
    print("\n[Step 3/6] Verifying Saved Active Anthropometric Measurements...")
    t0 = time.perf_counter()
    r3 = client.get(f"/api/v1/profiles/{profile_id}/measurements", headers=user_headers)
    assert r3.status_code == 200, f"Failed to retrieve measurements: {r3.text}"
    measurements = r3.json()["measurements"]
    timeline["step_3_verify_measurements_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    for code, m in measurements.items():
        print(f"  * {code:32s}: {m['value_cm']:6.2f} cm [{m['acquisition_method']}] ({m['assessment_state']})")

    # -------------------------------------------------------------------------
    # STEP 4: Stream Private Binary GLB
    # -------------------------------------------------------------------------
    print("\n[Step 4/6] Streaming Private Binary GLB via Content-Addressed Endpoint...")
    t0 = time.perf_counter()
    r4 = client.get(f"/api/v1/avatar/assets/{avatar_id}.glb", headers=user_headers)
    assert r4.status_code == 200, f"Failed to stream GLB: {r4.status_code}"
    assert len(r4.content) == avatar_data["size_bytes"]
    timeline["step_4_stream_glb_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    print(f"  -> Content-Type: {r4.headers['content-type']}")
    print(f"  -> Cache-Control: {r4.headers['cache-control']}")
    print(f"  -> ETag: {r4.headers.get('etag')}")
    print(f"  -> Bytes Transferred: {len(r4.content):,} bytes in {timeline['step_4_stream_glb_ms']} ms")

    # -------------------------------------------------------------------------
    # STEP 5: Register Merchant Garment with Size Specifications
    # -------------------------------------------------------------------------
    print("\n[Step 5/6] Registering Merchant Garment Specification & Finished Sizes...")
    t0 = time.perf_counter()
    garment_payload = {
        "sku": "TSH-WW-CREW-001",
        "title": "Everyday Heavyweight Crewneck Tee",
        "category": "t_shirt",
        "fabric_properties": {
            "fibre_composition": {"cotton": 1.0},
            "mechanical_stretch_pct": 0.015,
            "stretch_recovery_pct": 0.90,
            "stretch_direction": "rigid_zero",
        },
    }
    r5 = client.post("/api/v1/garments", headers=brand_headers, json=garment_payload)
    assert r5.status_code == 201, f"Failed to create garment: {r5.text}"
    garment_id = r5.json()["garment_id"]

    # Add S, M, L, XL sizes
    sizes_data = [
        ("XS", 1, {"garment_half_chest_width": 41.5, "garment_shoulder_seam_width": 37.5, "garment_back_length": 64.0}),
        ("S", 2, {"garment_half_chest_width": 44.0, "garment_shoulder_seam_width": 39.5, "garment_back_length": 66.5}),
        ("M", 3, {"garment_half_chest_width": 46.5, "garment_shoulder_seam_width": 41.5, "garment_back_length": 69.0}),
        ("L", 4, {"garment_half_chest_width": 50.0, "garment_shoulder_seam_width": 44.0, "garment_back_length": 71.5}),
    ]

    for label, order, dims in sizes_data:
        size_payload = {
            "size_label": label,
            "sort_order": order,
            "measurements": [
                {
                    "dimension_code": code,
                    "value_cm": val,
                    "tolerance_cm": 1.00,
                    "measurement_procedure": "flat_relaxed_tabletop_bs_4952",
                    "provenance": "demonstration_fixture",
                }
                for code, val in dims.items()
            ],
        }
        r_size = client.post(f"/api/v1/garments/{garment_id}/sizes", headers=brand_headers, json=size_payload)
        assert r_size.status_code == 201, f"Failed to add size {label}: {r_size.text}"

    timeline["step_5_register_garment_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    print(f"  -> Garment ID: {garment_id} | SKU: {garment_payload['sku']}")
    print(f"  -> Sizes Registered: XS, S, M, L (with BS 4952 measurement provenance)")
    print(f"  -> Duration: {timeline['step_5_register_garment_ms']} ms")

    # -------------------------------------------------------------------------
    # STEP 6: Execute Honest Fit Evaluation
    # -------------------------------------------------------------------------
    print("\n[Step 6/6] Executing Honest Fit Evaluation (Regular Silhouette Preference)...")
    t0 = time.perf_counter()
    fit_payload = {
        "profile_id": profile_id,
        "garment_id": garment_id,
        "user_fit_preference": "regular",
    }
    r6 = client.post("/api/v1/fit/recommend", headers=user_headers, json=fit_payload)
    assert r6.status_code == 200, f"Failed to evaluate fit: {r6.text}"
    fit_data = r6.json()
    rec_id = fit_data["recommendation_id"]
    timeline["step_6_evaluate_fit_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)

    print(f"  -> Recommendation ID: {rec_id}")
    print(f"  -> Recommended Size: Size {fit_data['recommended_size']} (Provisional Score: {fit_data['composite_fit_score']:.1f} / 100)")
    print(f"  -> Status: {fit_data['status']}")
    if fit_data.get("alternative_size"):
        print(f"  -> Alternative Size: {fit_data['alternative_size']['size_label']} ({fit_data['alternative_size']['fit_summary']})")

    print("\n  Regional Fit Breakdown:")
    for comp in fit_data["regional_comparisons"]:
        print(f"    * {comp['region']:12s}: Ease {comp['ease_cm']:+6.2f} cm => {comp['classification'].upper():10s} | {comp['explanation']}")

    # Retrieve persisted recommendation
    r7 = client.get(f"/api/v1/fit/recommendations/{rec_id}", headers=user_headers)
    assert r7.status_code == 200
    persisted_rec = r7.json()
    assert persisted_rec["recommendation_id"] == rec_id

    # Export complete demonstration report
    demo_report = {
        "milestone": "Phase 6A Working Backend Vertical Slice",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "architecture": {
            "pattern": "Modular Monolith",
            "framework": "FastAPI",
            "orm": "SQLAlchemy 2.0",
            "database": "SQLite 3 (WAL mode) / PostgreSQL 16+ compatible DDL",
            "avatar_engine": "NAVER Anny v0.6.2",
            "fit_engine": "WearWise Honest Fit Rev 1.2.1",
        },
        "workflow_execution": {
            "profile": profile_data,
            "avatar": avatar_data,
            "active_measurements": measurements,
            "garment": {
                "garment_id": garment_id,
                "sku": garment_payload["sku"],
                "sizes_count": len(sizes_data),
            },
            "fit_recommendation": fit_data,
        },
        "benchmarks": timeline,
    }

    report_path = artifacts_dir / "phase6a_e2e_demo_report.json"
    report_path.write_text(json.dumps(demo_report, indent=2), encoding="utf-8")
    print(f"\n[OK] Wrote full demonstration report to {report_path}")

    # Copy to brain artifact directory as well
    brain_dir = Path(r"C:\Users\Lenovo\.gemini\antigravity\brain\c57b9fa6-3e23-4fa2-b534-c1f6bc625ad8\phase6a")
    brain_dir.mkdir(parents=True, exist_ok=True)
    (brain_dir / "phase6a_e2e_demo_report.json").write_text(json.dumps(demo_report, indent=2), encoding="utf-8")
    (brain_dir / "openapi.json").write_text((artifacts_dir / "openapi.json").read_text(encoding="utf-8"), encoding="utf-8")

    print("\n" + "=" * 80)
    print("  PHASE 6A VERTICAL SLICE DEMONSTRATION SUCCESSFUL")
    print("=" * 80)


if __name__ == "__main__":
    run_e2e_demonstration()
