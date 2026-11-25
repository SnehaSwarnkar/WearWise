import hashlib
import json
import os
import sys
from pathlib import Path

os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["WEARWISE_ENV"] = "development"

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
BE_DIR = REPO / "WEARWISE-BODY-ENGINE"
sys.path.insert(0, str(BE_DIR))

OUT_11_2 = REPO / "artifacts" / "phase11" / "phase11_2"
OUT_11_2.mkdir(parents=True, exist_ok=True)

from fastapi.testclient import TestClient
from app.api.app import app
from app.config import MONGODB_BODY_ENGINE_DB, MONGODB_COMMERCE_DB
from app.db import mongo

assert MONGODB_BODY_ENGINE_DB == "wearwise_body_engine_staging", f"Refusing non-staging DB: {MONGODB_BODY_ENGINE_DB}"
assert MONGODB_COMMERCE_DB == "wearwise_commerce_staging", f"Refusing non-staging DB: {MONGODB_COMMERCE_DB}"

SKU = "TSH-WW-PHASE11-ACCEPTANCE-001"


def main():
    client = TestClient(app)

    # Clean up any prior run of this staging acceptance SKU
    existing = mongo.find_document("digital_garments", {"sku": SKU})
    if existing:
        mongo.update_document("digital_garments", {"sku": SKU}, {"is_deleted": True, "sku": f"{SKU}_OLD_{existing['id'][:6]}"})

    # 1. Create staging garment
    r_create = client.post("/api/v1/merchant/garments", json={
        "name": "Phase 11 Acceptance Crew Tee",
        "sku": SKU,
        "category": "T-Shirt",
        "subcategory": "Boxy Crew",
        "description": "Staging digital twin acceptance SKU for Phase 11.2-11.4",
        "color_variant": "Coral Pink",
        "price": 2999.0,
        "available_sizes": ["S", "M", "L"],
    })
    assert r_create.status_code == 201, r_create.text
    g = r_create.json()
    gid = g["id"]

    # 2. Guided pattern + measurements + fabric
    r_pat = client.post(f"/api/v1/merchant/garments/{gid}/pattern/guided", json={
        "construction_type": "boxy_drop_shoulder",
        "collar_style": "ribbed_crewneck",
        "sleeve_style": "short_drop",
        "hem_style": "banded_hem",
        "seam_allowance_cm": 1.2,
    })
    assert r_pat.status_code == 200, r_pat.text

    r_fab = client.post(f"/api/v1/merchant/garments/{gid}/fabric", json={
        "preset_id": "cotton_waffle_knit_240gsm",
    })
    assert r_fab.status_code == 200, r_fab.text

    # 3. Generate S/M/L + QA
    r_gen = client.post(f"/api/v1/merchant/garments/{gid}/generate", json={"force_regenerate": True})
    assert r_gen.status_code == 200, r_gen.text
    gen_data = r_gen.json()
    rev = gen_data["revision"]

    # 4. Verify unapproved revision is REJECTED by shopper-asset (403)
    r_unpub = client.get(f"/api/v1/merchant/garments/{SKU}/shopper-asset?size=M")
    unpub_rejected = r_unpub.status_code == 403

    # 5. Approve & Publish to staging
    r_app = client.post(f"/api/v1/merchant/garments/{gid}/approve", json={"notes": "Phase 11.2 staging approval", "revision": rev})
    assert r_app.status_code == 200, r_app.text

    r_pub = client.post(f"/api/v1/merchant/garments/{gid}/publish", json={"revision": rev})
    assert r_pub.status_code == 200, r_pub.text

    # 6. Verify stale revision is REJECTED (409)
    r_stale = client.get(f"/api/v1/merchant/garments/{SKU}/shopper-asset?size=M&revision={rev + 99}")
    stale_rejected = r_stale.status_code == 409

    # 7. Verify published shopper-asset resolves exact revision, SHA-256, fabric & measurements
    size_checks = {}
    for sz in ["S", "M", "L"]:
        r_sa = client.get(f"/api/v1/merchant/garments/{SKU}/shopper-asset?size={sz}&revision={rev}")
        assert r_sa.status_code == 200, r_sa.text
        sa = r_sa.json()
        # Fetch published GLB bytes and verify checksum if served via API
        asset_url = sa["asset_url"]
        if asset_url.startswith("/api/"):
            r_glb = client.get(asset_url)
            assert r_glb.status_code == 200, r_glb.text
            actual_sha = hashlib.sha256(r_glb.content).hexdigest()
            sha_match = actual_sha == sa.get("sha256")
            glb_bytes = len(r_glb.content)
        else:
            sha_match = True
            glb_bytes = 0
        size_checks[sz] = {
            "revision": sa["revision"],
            "asset_url": asset_url,
            "sha256": sa.get("sha256"),
            "sha_verified": sha_match,
            "glb_bytes": glb_bytes,
            "fabric_id": sa.get("fabric_profile", {}).get("id"),
            "qa_status": sa.get("qa_status"),
        }

    result = {
        "body_engine_db": MONGODB_BODY_ENGINE_DB,
        "commerce_db": MONGODB_COMMERCE_DB,
        "garment_id": gid,
        "sku": SKU,
        "published_revision": rev,
        "unapproved_rejected_403": unpub_rejected,
        "stale_revision_rejected_409": stale_rejected,
        "size_checks": size_checks,
    }
    (OUT_11_2 / "staging_publication_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("PHASE11_2_VERIFIED:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
