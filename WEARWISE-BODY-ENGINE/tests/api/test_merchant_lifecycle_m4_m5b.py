import io
import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"

from app.api.app import app
from app.db import mongo

client = TestClient(app)

BRAND_A = "e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e"
BRAND_B = "22222222-3333-4444-5555-666666666666"


def _png_bytes():
    im = Image.new("RGB", (32, 32), (240, 130, 145))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_body_engine_staging_isolation():
    res = client.get("/health")
    assert res.status_code == 200
    mdb = res.json()["mongodb"]
    assert mdb["database"] == "wearwise_body_engine_staging"
    assert mdb["database"] != "wearwise_body_engine"


def test_ownership_lifecycle_negative_and_concurrency():
    sku = f"TSH-WW-PYTEST-{uuid.uuid4().hex[:6].upper()}"
    hdr_a = {"X-Brand-Id": BRAND_A}
    hdr_b = {"X-Brand-Id": BRAND_B}
    gid = None

    try:
        # 1. Create draft + duplicate SKU 409
        r_c = client.post(
            "/api/v1/merchant/garments",
            json={"name": "Pytest Lifecycle Tee", "sku": sku, "price": 1999},
            headers=hdr_a,
        )
        assert r_c.status_code == 201
        gid = r_c.json()["id"]

        r_dup = client.post(
            "/api/v1/merchant/garments",
            json={"name": "Dup", "sku": sku, "price": 999},
            headers=hdr_a,
        )
        assert r_dup.status_code == 409

        # 2. Upload valid image + corrupt image rejection
        r_img = client.post(
            f"/api/v1/merchant/garments/{gid}/images",
            data={"viewpoint": "front", "role": "both"},
            files={"file": ("front.png", _png_bytes(), "image/png")},
            headers=hdr_a,
        )
        assert r_img.status_code == 200
        img_id = r_img.json()["uploaded_image"]["id"]

        r_bad_img = client.post(
            f"/api/v1/merchant/garments/{gid}/images",
            data={"viewpoint": "back", "role": "technical_reference"},
            files={"file": ("bad.png", b"NOT_PNG", "image/png")},
            headers=hdr_a,
        )
        assert r_bad_img.status_code == 400

        # 3. Publish before generation/approval fails
        r_pub_early = client.post(
            f"/api/v1/merchant/garments/{gid}/publish",
            json={"publisher_id": "tester"},
            headers=hdr_a,
        )
        assert r_pub_early.status_code == 400

        # 4. Generate rev1 + idempotent hit
        r_g1 = client.post(f"/api/v1/merchant/garments/{gid}/generate", headers=hdr_a)
        assert r_g1.status_code == 200
        g1 = r_g1.json()
        assert g1["revision"] == 1
        assert g1["qa_report"]["overall_status"] == "PASSED"

        r_g1_idem = client.post(f"/api/v1/merchant/garments/{gid}/generate", headers=hdr_a)
        assert r_g1_idem.status_code == 200
        assert r_g1_idem.json()["idempotent_hit"] is True

        # 5. Cross-owner isolation across ALL merchant resources
        for method, path, body in [
            ("GET", f"/api/v1/merchant/garments/{gid}", None),
            ("GET", f"/api/v1/merchant/garments/{gid}/images/{img_id}/content", None),
            ("GET", f"/api/v1/merchant/garments/{gid}/revisions/1/assets/M", None),
            ("GET", f"/api/v1/merchant/garments/{gid}/jobs", None),
            ("GET", f"/api/v1/merchant/garments/{gid}/qa-report", None),
            ("POST", f"/api/v1/merchant/garments/{gid}/approve", {"principal_id": "attacker"}),
            ("POST", f"/api/v1/merchant/garments/{gid}/publish", {"publisher_id": "attacker"}),
            ("POST", f"/api/v1/merchant/garments/{gid}/rollback", {"target_revision": 1}),
        ]:
            resp = client.request(method, path, json=body, headers=hdr_b)
            assert resp.status_code == 403, f"Expected 403 for {method} {path}, got {resp.status_code}"

        # 6. Approve & concurrent publish attempts
        r_ap = client.post(
            f"/api/v1/merchant/garments/{gid}/approve",
            json={"principal_id": "brand_director", "approval_notes": "Approved"},
            headers=hdr_a,
        )
        assert r_ap.status_code == 200

        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = [
                ex.submit(client.post, f"/api/v1/merchant/garments/{gid}/publish", json={"publisher_id": "pub_1"}, headers=hdr_a),
                ex.submit(client.post, f"/api/v1/merchant/garments/{gid}/publish", json={"publisher_id": "pub_2"}, headers=hdr_a),
            ]
            pubs = [f.result() for f in futs]
        assert all(p.status_code == 200 for p in pubs)

        # 7. Nonexistent rollback fails cleanly
        r_bad_rb = client.post(
            f"/api/v1/merchant/garments/{gid}/rollback",
            json={"target_revision": 99, "publisher_id": "pub"},
            headers=hdr_a,
        )
        assert r_bad_rb.status_code == 400
    finally:
        # Cleanup staging test doc and temporary artifact directories
        for col in [
            "digital_garments", "garment_revisions", "garment_generation_jobs",
            "garment_assets", "garment_qa_reports", "garment_package_manifests",
            "garment_approval_events", "garment_publications", "garment_audit_events",
        ]:
            c = mongo.get_collection(col)
            if c is not None:
                c.delete_many({"sku": sku})
        cp = mongo.get_commerce_collection("catalog_publications")
        if cp is not None:
            cp.delete_many({"sku": sku})
        root = Path(__file__).resolve().parents[2]
        shutil.rmtree(root / "artifacts" / "merchant_private" / BRAND_A / sku, ignore_errors=True)
        shutil.rmtree(root / "artifacts" / "published_catalog" / sku, ignore_errors=True)
        if gid:
            shutil.rmtree(root / "artifacts" / "merchant_uploads" / gid, ignore_errors=True)
