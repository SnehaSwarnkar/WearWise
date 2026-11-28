import os
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"

COMMERCE_ROOT = Path(__file__).resolve().parents[1]
if str(COMMERCE_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMERCE_ROOT))

from app.main import app
from app import database as db
from app.routers import products as products_router

client = TestClient(app)


def test_category_filtering_and_dual_mode_capabilities(monkeypatch):
    products_router.reset_vton_health_cache()
    monkeypatch.delenv("FASHN_API_KEY", raising=False)
    monkeypatch.delenv("VTON_API_URL", raising=False)
    monkeypatch.delenv("VTON_API_KEY", raising=False)
    monkeypatch.setenv("VTON_PROVIDER_MODE", "disabled")

    all_res = client.get("/api/products/")
    assert all_res.status_code == 200
    all_items = all_res.json()
    assert len(all_items) >= 9

    for cat in ["Tops", "T-Shirts", "Shirts", "Trousers", "Jeans", "Skirts", "Dresses", "Jackets"]:
        r = client.get(f"/api/products/?category={cat}")
        assert r.status_code == 200
        assert len(r.json()) >= 1, f"Expected at least 1 product in category {cat}"

    # When VTON provider is unconfigured, seller intent is separated from platform service readiness:
    # Seller enabled both on TSH-WW-CREW-001, 3D is ready, Image is disabled due to missing VTON service
    r_both = client.get("/api/products/sku/TSH-WW-CREW-001")
    assert r_both.status_code == 200
    caps_both = r_both.json()["tryOnCapabilities"]
    assert caps_both["mode"] == "IMAGE_AND_THREE_D"
    assert caps_both["sellerImageTryOnEnabled"] is True
    assert caps_both["sellerThreeDTryOnEnabled"] is True
    assert caps_both["threeDTryOnEnabled"] is True
    assert caps_both["imageTryOnEnabled"] is False
    assert caps_both["vtonServiceConfigured"] is False

    # IMAGE_ONLY item disables both 3D (seller disabled) and Image (provider unavailable or missing photos)
    r_img = client.get("/api/products/sku/TSH-WW-OVERSIZE-002")
    assert r_img.status_code == 200
    caps_img = r_img.json()["tryOnCapabilities"]
    assert caps_img["mode"] == "IMAGE_ONLY"
    assert caps_img["sellerImageTryOnEnabled"] is True
    assert caps_img["threeDTryOnEnabled"] is False
    assert caps_img["threeDDisabledReason"]

    # When VTON service IS configured & healthy + seller photo exists -> imageTryOnReady becomes True
    monkeypatch.setenv("VTON_PROVIDER_MODE", "auto")
    monkeypatch.setenv("VTON_PROVIDER", "fashn")
    monkeypatch.setenv("FASHN_API_KEY", "test-key")
    products_router.reset_vton_health_cache()

    test_sku = f"SHIRT-READY-{uuid.uuid4().hex[:6].upper()}"
    db.insert(
        "catalog_publications",
        {
            "sku": test_sku,
            "garment_id": "g-img-ready",
            "brand_id": "b-test",
            "name": "Photo Ready Shirt",
            "category": "Shirts",
            "price": 1299,
            "status": "published",
            "active_revision": 1,
            "published_version": "v1.0",
            "try_on_mode": "IMAGE_ONLY",
            "size_variants": {},
            "storefront_images": [{"id": "front-1", "viewpoint": "front", "url": "/garments/garment_texture_diffuse.png"}],
            "qa_summary": {"overall_status": "PASSED"},
        },
    )
    try:
        r_ready = client.get(f"/api/products/sku/{test_sku}")
        assert r_ready.status_code == 200
        caps_ready = r_ready.json()["tryOnCapabilities"]
        assert caps_ready["vtonServiceConfigured"] is True
        assert caps_ready["vtonServiceHealthy"] is True
        assert caps_ready["imageTryOnEnabled"] is True
        assert caps_ready["imageTryOnReady"] is True
        assert caps_ready["threeDTryOnEnabled"] is False
    finally:
        db.delete_one("catalog_publications", sku=test_sku)
        products_router.reset_vton_health_cache()


def test_fail_closed_3d_capability_when_assets_missing():
    fake_sku = f"TSH-WW-FAIL3D-{uuid.uuid4().hex[:6].upper()}"
    db.insert(
        "catalog_publications",
        {
            "sku": fake_sku,
            "garment_id": "g-fail",
            "brand_id": "b-test",
            "name": "Missing 3D Listing",
            "category": "Tops",
            "price": 1499,
            "status": "published",
            "active_revision": 1,
            "published_version": "v1.0",
            "try_on_mode": "THREE_D_ONLY",
            "size_variants": {},
            "storefront_images": [],
        },
    )
    try:
        res = client.get(f"/api/products/sku/{fake_sku}")
        assert res.status_code == 200
        caps = res.json()["tryOnCapabilities"]
        assert caps["threeDTryOnEnabled"] is False
        assert caps["threeDDisabledReason"]
        assert caps["imageTryOnEnabled"] is False
    finally:
        db.delete_one("catalog_publications", sku=fake_sku)


def test_real_customer_reviews_empty_state_and_submission():
    target_sku = "SKT-WW-MIDI-009"
    if db.is_mongo_active():
        db.get_db()["product_reviews"].delete_many({"sku": target_sku})

    r_empty = client.get(f"/api/products/sku/{target_sku}/reviews")
    assert r_empty.status_code == 200
    empty_data = r_empty.json()
    assert empty_data["review_count"] == 0
    assert empty_data["average_rating"] is None
    assert empty_data["reviews"] == []

    r_post = client.post(
        f"/api/products/sku/{target_sku}/reviews",
        json={
            "rating": 5,
            "comment": "Crisp fabric and flattering waist fit.",
            "author_name": "Riya M.",
            "size_purchased": "M",
            "fit_feedback": "True to Size",
        },
    )
    assert r_post.status_code == 201
    created_id = r_post.json()["id"]
    try:
        r_list = client.get(f"/api/products/sku/{target_sku}/reviews")
        assert r_list.status_code == 200
        body = r_list.json()
        assert body["review_count"] == 1
        assert body["average_rating"] == 5.0
        assert body["reviews"][0]["comment"] == "Crisp fabric and flattering waist fit."
        assert body["reviews"][0]["verified_purchase"] is False
    finally:
        db.delete_one("product_reviews", id=created_id)
