import io
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict

from fastapi.testclient import TestClient
from PIL import Image

os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"

from app.api.app import app
from app.api.v1 import vton as vton_router
from app.db import mongo
from app.services.person_image_service import PersonImageService
from app.services.vton_job_service import VTONJobService
from app.services.vton_provider import BaseVTONProvider

client = TestClient(app)

BRAND_A = "e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e"
USER_1 = "11111111-2222-3333-4444-555555555555"
USER_2 = "99999999-8888-7777-6666-555555555555"


def _real_like_photo_bytes(with_exif: bool = False) -> bytes:
    # Textured multi-color RGB photo (>10 KB, >= 256x256, >16 colors) so avatar heuristic accepts it
    im = Image.new("RGB", (320, 384))
    px = im.load()
    for y in range(384):
        for x in range(320):
            px[x, y] = ((x * 3 + y) % 256, (y * 5 + x) % 256, (x * y + 17) % 256)
    buf = io.BytesIO()
    if with_exif:
        exif = Image.Exif()
        exif[271] = "TestPhoneMaker"
        exif[272] = "CameraModelX"
        im.save(buf, format="JPEG", quality=92, exif=exif)
    else:
        im.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


class _FakeExternalVTONProvider(BaseVTONProvider):
    def is_ready(self):
        return True, ""

    def get_provider_metadata(self):
        return {"available": True, "status": "ready", "provider_name": "MockExternalVTON"}

    def generate_multiview(self, person_image_path: str, garment_sku: str, garment_metadata: Dict) -> Dict[str, Image.Image]:
        return {"front": Image.new("RGB", (256, 256), (200, 120, 150))}


def test_vton_provider_honest_unavailable_and_validation(tmp_path):
    r_prov = client.get("/api/v1/try-on/vton/providers")
    assert r_prov.status_code == 200
    prov = r_prov.json()
    assert prov["available"] is False
    assert prov["status"] == "provider_unavailable"

    photo = _real_like_photo_bytes(with_exif=True)
    # Missing consent -> 422
    r_no_consent = client.post(
        "/api/v1/try-on/vton/jobs",
        data={"garment_sku": "TSH-WW-CREW-001", "consent": "false"},
        files={"file": ("selfie.jpg", photo, "image/jpeg")},
        headers={"X-User-Id": USER_1},
    )
    assert r_no_consent.status_code == 422

    # Unconfigured external VTON -> honest 503 with zero naive overlay fallback
    r_unavail = client.post(
        "/api/v1/try-on/vton/jobs",
        data={"garment_sku": "TSH-WW-CREW-001", "consent": "true"},
        files={"file": ("selfie.jpg", photo, "image/jpeg")},
        headers={"X-User-Id": USER_1},
    )
    assert r_unavail.status_code == 503
    assert r_unavail.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"

    # EXIF stripping verification directly on PersonImageService
    svc = PersonImageService(storage_dir=tmp_path)
    processed = svc.validate_and_process(photo, "selfie.jpg", user_consent=True)
    saved_im = Image.open(processed["file_path"])
    assert len(saved_im.getexif()) == 0
    saved_im.close()
    svc.delete_photo(processed["file_path"])
    assert not Path(processed["file_path"]).exists()


def test_fashn_provider_category_mapping_and_health(monkeypatch):
    from app.services.vton_provider import HonestVTONProviderAdapter, _map_wearwise_category_to_fashn

    assert _map_wearwise_category_to_fashn("Skirts") == "bottoms"
    assert _map_wearwise_category_to_fashn("Jeans") == "bottoms"
    assert _map_wearwise_category_to_fashn("Dresses") == "one-pieces"
    assert _map_wearwise_category_to_fashn("Shirts") == "tops"

    adapter = HonestVTONProviderAdapter()
    assert adapter.is_ready()[0] is False
    monkeypatch.setenv("VTON_PROVIDER", "fashn")
    monkeypatch.setenv("FASHN_API_KEY", "test-fashn-key-placeholder")
    meta = adapter.get_provider_metadata()
    assert meta["configured"] is True
    assert meta["available"] is True
    assert meta["provider_type"] == "fashn"


def test_vton_ownership_isolation_and_temp_photo_cleanup(tmp_path):
    orig_provider = vton_router._provider
    orig_service = vton_router._job_service
    fake_provider = _FakeExternalVTONProvider()
    vton_router._provider = fake_provider
    vton_router._job_service = VTONJobService(
        person_service=PersonImageService(storage_dir=tmp_path / "uploads"),
        provider=fake_provider,
    )
    try:
        photo = _real_like_photo_bytes()
        r_create = client.post(
            "/api/v1/try-on/vton/jobs",
            data={"garment_sku": "TSH-WW-CREW-001", "consent": "true"},
            files={"file": ("me.jpg", photo, "image/jpeg")},
            headers={"X-User-Id": USER_1},
        )
        assert r_create.status_code == 202
        job_id = r_create.json()["job_id"]

        # Wait briefly for background thread completion
        for _ in range(25):
            st = client.get(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_1})
            if st.status_code == 200 and st.json()["status"] == "completed":
                break
            time.sleep(0.1)

        st_done = client.get(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_1})
        assert st_done.status_code == 200
        assert st_done.json()["status"] == "completed"
        assert st_done.json()["temp_upload_deleted"] is True
        assert list((tmp_path / "uploads").glob("*")) == []

        res_owner = client.get(f"/api/v1/try-on/vton/jobs/{job_id}/results", headers={"X-User-Id": USER_1})
        assert res_owner.status_code == 200
        front_url = res_owner.json()["views"]["front"]["url"]

        r_img_owner = client.get(front_url, headers={"X-User-Id": USER_1})
        assert r_img_owner.status_code == 200
        assert "no-store" in (r_img_owner.headers.get("cache-control") or "")

        # Other user cannot inspect status, results, image, or delete the job
        assert client.get(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_2}).status_code == 403
        assert client.get(f"/api/v1/try-on/vton/jobs/{job_id}/results", headers={"X-User-Id": USER_2}).status_code == 403
        assert client.get(front_url, headers={"X-User-Id": USER_2}).status_code == 403
        assert client.delete(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_2}).status_code == 403

        # Owner deletes job & assets cleanly
        r_del = client.delete(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_1})
        assert r_del.status_code == 200
        assert client.get(f"/api/v1/try-on/vton/jobs/{job_id}", headers={"X-User-Id": USER_1}).status_code == 404
    finally:
        vton_router._provider = orig_provider
        vton_router._job_service = orig_service


def test_seller_image_only_publish_without_3d_and_3d_fail_closed():
    sku = f"SHIRT-P12-{uuid.uuid4().hex[:6].upper()}"
    hdr = {"X-Brand-Id": BRAND_A}
    im = Image.new("RGB", (64, 64), (120, 180, 220))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    try:
        r_create = client.post(
            "/api/v1/merchant/garments",
            json={"name": "Image Only Linen Shirt", "sku": sku, "category": "Shirts", "price": 1599, "try_on_mode": "IMAGE_ONLY"},
            headers=hdr,
        )
        assert r_create.status_code == 201
        gid = r_create.json()["id"]

        # Without a front photo, preparing Image Try-On fails closed
        r_no_photo = client.post(f"/api/v1/merchant/garments/{gid}/prepare-image-tryon", headers=hdr)
        assert r_no_photo.status_code == 400

        # Upload storefront front photo -> prepare -> approve -> publish WITHOUT generating 3D
        r_up = client.post(
            f"/api/v1/merchant/garments/{gid}/images",
            data={"viewpoint": "front", "role": "storefront_gallery"},
            files={"file": ("front.png", png_bytes, "image/png")},
            headers=hdr,
        )
        assert r_up.status_code == 200

        r_prep = client.post(f"/api/v1/merchant/garments/{gid}/prepare-image-tryon", headers=hdr)
        assert r_prep.status_code == 200

        r_app = client.post(
            f"/api/v1/merchant/garments/{gid}/approve",
            json={"principal_id": "seller_owner", "approval_notes": "Photos ready"},
            headers=hdr,
        )
        assert r_app.status_code == 200

        r_pub = client.post(
            f"/api/v1/merchant/garments/{gid}/publish",
            json={"publisher_id": "seller_owner"},
            headers=hdr,
        )
        assert r_pub.status_code == 200
        pub_data = r_pub.json()
        assert pub_data["try_on_mode"] == "IMAGE_ONLY"
        assert pub_data["try_on_capabilities"]["imageTryOnEnabled"] is True
        assert pub_data["try_on_capabilities"]["threeDTryOnEnabled"] is False

        # Switching to THREE_D_ONLY without 3D assets must block republishing fail-closed
        r_mode = client.post(
            f"/api/v1/merchant/garments/{gid}/try-on-mode",
            json={"try_on_mode": "THREE_D_ONLY"},
            headers=hdr,
        )
        assert r_mode.status_code == 200
        r_pub_blocked = client.post(
            f"/api/v1/merchant/garments/{gid}/publish",
            json={"publisher_id": "seller_owner"},
            headers=hdr,
        )
        assert r_pub_blocked.status_code == 400
    finally:
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
        shutil.rmtree(root / "artifacts" / "published_catalog" / sku, ignore_errors=True)
        shutil.rmtree(root / "artifacts" / "merchant_uploads" / gid, ignore_errors=True)
