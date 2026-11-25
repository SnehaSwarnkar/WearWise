"""
GET /api/products                                    — list all products (static + published MongoDB catalog)
GET /api/products/sku/{sku}                          — resolve published digital garment product by SKU
GET /api/products/sku/{sku}/reviews                  — list customer reviews for a SKU
POST /api/products/sku/{sku}/reviews                 — submit a customer review for a SKU
GET /api/products/sku/{sku}/revisions/{rev}/assets/{size} — immutable revision-pinned published GLB stream
GET /api/products/sku/{sku}/revisions/{rev}/images/{file} — published storefront-only gallery image
GET /api/products/{id}                               — single product detail
"""

import hashlib
import os
import time
import urllib.request
import json as _json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from app import database as db
from app.core.security import CANONICAL_DEFAULT_BRAND_ID, get_optional_authenticated_user
from app.schemas.products import Product, ReviewCreateRequest

router = APIRouter(prefix="/api/products", tags=["Products"])

MONOREPO_ROOT = Path(__file__).resolve().parents[3]
PUBLISHED_CATALOG_ROOT = MONOREPO_ROOT / "WEARWISE-BODY-ENGINE" / "artifacts" / "published_catalog"

VALID_TRY_ON_MODES = {"IMAGE_ONLY", "THREE_D_ONLY", "IMAGE_AND_THREE_D"}

_vton_status_cache: dict[str, Any] = {"ts": 0.0, "data": None}


def reset_vton_health_cache() -> None:
    _vton_status_cache["ts"] = 0.0
    _vton_status_cache["data"] = None


def get_platform_vton_status() -> dict[str, Any]:
    """
    Checks actual platform VTON provider configuration and health cleanly.
    Strictly separate from seller-enabled flags so unavailable VTON shows disabled UI before upload.
    """
    mode_override = os.getenv("VTON_PROVIDER_MODE", "auto").strip().lower()
    if mode_override == "disabled":
        return {
            "configured": False,
            "healthy": False,
            "status": "provider_unavailable",
            "reason": "Image Try-On service is paused in this environment.",
        }

    fashn_key = os.getenv("FASHN_API_KEY", "").strip()
    vton_url = os.getenv("VTON_API_URL", "").strip()
    vton_key = os.getenv("VTON_API_KEY", "").strip()
    provider_type = os.getenv("VTON_PROVIDER", "").strip().lower()

    if (provider_type == "fashn" and (fashn_key or vton_key)) or fashn_key or vton_url:
        return {
            "configured": True,
            "healthy": True,
            "status": "ready",
            "reason": None,
        }

    now = time.monotonic()
    if _vton_status_cache["data"] is not None and (now - _vton_status_cache["ts"]) < 5.0:
        return _vton_status_cache["data"]

    body_engine_url = os.getenv("BODY_ENGINE_URL", "http://127.0.0.1:8000").rstrip("/")
    result = {
        "configured": False,
        "healthy": False,
        "status": "provider_unavailable",
        "reason": "Image Try-On service is currently unavailable until an external AI try-on provider is connected.",
    }
    try:
        with urllib.request.urlopen(f"{body_engine_url}/api/v1/try-on/vton/providers", timeout=0.4) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict) and payload.get("available"):
                result = {
                    "configured": True,
                    "healthy": True,
                    "status": "ready",
                    "reason": None,
                }
            elif isinstance(payload, dict) and payload.get("unavailable_reason"):
                result["reason"] = payload["unavailable_reason"]
    except Exception:
        pass

    _vton_status_cache["ts"] = now
    _vton_status_cache["data"] = result
    return result

CATEGORY_ALIASES = {
    "tops": {"tops", "top", "t-shirt", "t-shirts", "tee", "tees"},
    "t-shirts": {"tops", "t-shirt", "t-shirts", "tee", "tees"},
    "shirts": {"shirts", "shirt"},
    "trousers": {"trousers", "trouser", "pants", "pant"},
    "jeans": {"jeans", "jean", "denim"},
    "skirts": {"skirts", "skirt"},
    "dresses": {"dresses", "dress"},
    "jackets": {"jackets", "jacket", "outerwear"},
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _stable_sku_id(sku: str) -> int:
    return 1000 + (int(hashlib.sha256(sku.encode("utf-8")).hexdigest()[:6], 16) % 900000)


def _normalize_mode(mode: Optional[str], has_3d_assets: bool) -> str:
    if mode and str(mode).upper() in VALID_TRY_ON_MODES:
        return str(mode).upper()
    return "IMAGE_AND_THREE_D" if has_3d_assets else "IMAGE_ONLY"


def build_try_on_capabilities(
    mode: Optional[str],
    has_3d_assets: bool,
    has_photos: bool = True,
    image_prep_passed: bool = True,
    vton_status: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Computes server-authoritative dual-mode capabilities cleanly separating:
      1. Seller-selected options & prepared product assets
      2. Platform VTON provider configuration and health
    Image Try-On becomes ready ONLY when all 4 gates pass.
    """
    effective_mode = _normalize_mode(mode, has_3d_assets)
    image_requested = effective_mode in ("IMAGE_ONLY", "IMAGE_AND_THREE_D")
    three_d_requested = effective_mode in ("THREE_D_ONLY", "IMAGE_AND_THREE_D")

    vton = vton_status if vton_status is not None else get_platform_vton_status()
    vton_configured = bool(vton.get("configured", False))
    vton_healthy = bool(vton.get("healthy", False))

    image_assets_ready = bool(has_photos and image_prep_passed)
    image_enabled = bool(image_requested and image_assets_ready and vton_configured and vton_healthy)
    three_d_enabled = bool(three_d_requested and has_3d_assets)

    image_reason: Optional[str] = None
    if not image_requested:
        image_reason = "The seller configured this item exclusively for Interactive 3D Try-On."
    elif not image_assets_ready:
        image_reason = "The seller has not uploaded storefront photos needed for Image Try-On."
    elif not (vton_configured and vton_healthy):
        image_reason = vton.get("reason") or (
            "Image Try-On service is currently unavailable until an external AI try-on provider is connected."
        )

    three_d_reason: Optional[str] = None
    if not three_d_requested:
        three_d_reason = "The seller has not enabled Interactive 3D Try-On for this item."
    elif not has_3d_assets:
        three_d_reason = "3D garment model assets have not been approved for this item yet."

    return {
        "mode": effective_mode,
        "sellerImageTryOnEnabled": image_requested,
        "sellerThreeDTryOnEnabled": three_d_requested,
        "imageAssetsReady": image_assets_ready,
        "threeDAssetsReady": bool(has_3d_assets),
        "vtonServiceConfigured": vton_configured,
        "vtonServiceHealthy": vton_healthy,
        "vtonServiceStatus": vton.get("status", "provider_unavailable"),
        "imageTryOnEnabled": image_enabled,
        "threeDTryOnEnabled": three_d_enabled,
        "imageTryOnReady": image_enabled,
        "threeDTryOnReady": three_d_enabled,
        "imageDisabledReason": image_reason,
        "threeDDisabledReason": three_d_reason,
    }


def _review_stats_for_sku(sku: Optional[str]) -> tuple[Optional[float], int]:
    if not sku:
        return None, 0
    rows = db.filter_by("product_reviews", sku=sku)
    if not rows:
        return None, 0
    ratings = [int(r.get("rating", 0)) for r in rows if r.get("rating")]
    if not ratings:
        return None, 0
    return round(sum(ratings) / len(ratings), 1), len(ratings)


def _enrich_product(prod: dict) -> dict:
    sku = prod.get("sku")
    size_variants = prod.get("size_variants") or {}
    has_3d = bool(size_variants) and any(
        isinstance(v, dict) and bool(v.get("asset_url")) for v in size_variants.values()
    )
    has_photos = bool(prod.get("image") or prod.get("storefront_images") or prod.get("has_storefront_photos"))
    caps = build_try_on_capabilities(prod.get("try_on_mode"), has_3d_assets=has_3d, has_photos=has_photos)
    avg, cnt = _review_stats_for_sku(sku)
    return {
        **prod,
        "available_sizes": prod.get("available_sizes") or ["S", "M", "L"],
        "seller_name": prod.get("seller_name") or prod.get("brand") or "WEARWISE EDIT",
        "try_on_mode": caps["mode"],
        "tryOnCapabilities": caps,
        "rating_average": avg,
        "review_count": cnt,
    }


def _pub_doc_to_product(pub: dict) -> dict:
    sku = pub["sku"]
    storefront_imgs = pub.get("storefront_images") or []
    lead_img = storefront_imgs[0]["url"] if storefront_imgs else None
    size_variants = pub.get("size_variants") or {}
    has_3d = bool(size_variants) and any(
        isinstance(v, dict) and bool(v.get("asset_url")) for v in size_variants.values()
    )
    has_photos = bool(storefront_imgs or lead_img)
    qa_status = str((pub.get("qa_summary") or {}).get("overall_status") or "PASSED").upper()
    image_prep_passed = qa_status in ("PASSED", "WARNING")
    caps = build_try_on_capabilities(
        pub.get("try_on_mode"),
        has_3d_assets=has_3d,
        has_photos=has_photos,
        image_prep_passed=image_prep_passed,
    )

    avg, cnt = _review_stats_for_sku(sku)
    raw_colors = pub.get("colors") or ([pub.get("color_variant")] if pub.get("color_variant") else ["#ff3d9a", "#ffffff", "#1d1d1d"])
    clean_colors = [c for c in raw_colors if isinstance(c, str) and c.strip()] or ["#1d1d1d"]

    return {
        "id": _stable_sku_id(sku),
        "name": pub.get("name", sku),
        "category": pub.get("category", "Tops"),
        "price": int(round(float(pub.get("price", 2999)))),
        "match": "Verified 3D Fit" if has_3d else "Photo Try-On Ready",
        "className": "product-pink",
        "colors": clean_colors,
        "image": lead_img,
        "brand": pub.get("seller_name") or "WEARWISE STUDIO",
        "brand_id": pub.get("brand_id") or CANONICAL_DEFAULT_BRAND_ID,
        "seller_name": pub.get("seller_name") or "WEARWISE STUDIO",
        "description": pub.get("description") or f"Published {pub.get('published_version', 'v1.0')} garment listing.",
        "sku": sku,
        "published_revision": pub.get("active_revision"),
        "published_version": pub.get("published_version"),
        "available_sizes": pub.get("available_sizes", ["S", "M", "L"]),
        "size_variants": size_variants,
        "measurement_chart": pub.get("measurement_chart"),
        "material_profile": pub.get("material_profile"),
        "storefront_images": storefront_imgs,
        "qa_summary": pub.get("qa_summary"),
        "try_on_mode": caps.get("mode", "IMAGE_AND_THREE_D"),
        "tryOnCapabilities": caps,
        "rating_average": avg,
        "review_count": cnt,
    }


def _list_published_products() -> list[dict]:
    if not db.is_mongo_active():
        return []
    cdb = db.get_db()
    if cdb is None:
        return []
    docs = list(cdb["catalog_publications"].find({"status": "published"}, {"_id": 0}))
    return [_pub_doc_to_product(d) for d in docs]

# Static product catalogue — preserves baseline IDs & prices while adding dual-mode capabilities
PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "Cherry Baby Tee",
        "category": "Tops",
        "price": 799,
        "match": "94% Style Match",
        "className": "product-pink",
        "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
        "image": None,
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "A boxy crew baby tee in cherry pink crafted in 220 GSM combed cotton. Supports both Photo Try-On and Interactive 3D Try-On.",
        "sku": "TSH-WW-CREW-001",
        "try_on_mode": "IMAGE_AND_THREE_D",
        "available_sizes": ["S", "M", "L"],
        "size_variants": {
            "S": {"asset_url": "/garments/TSH-WW-CREW-001_S.glb"},
            "M": {"asset_url": "/garments/TSH-WW-CREW-001_M.glb"},
            "L": {"asset_url": "/garments/TSH-WW-CREW-001_L.glb"},
        },
        "storefront_images": [],
    },
    {
        "id": 2,
        "name": "Cloud Oversized Shirt",
        "category": "Tops",
        "price": 1199,
        "match": "89% Style Match",
        "className": "product-lime",
        "colors": ["#d8ff3f", "#ffffff", "#8d6bff"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "A relaxed oversized shirt in citrusy lime poplin. Easy to wear, hard to ignore.",
        "sku": "TSH-WW-OVERSIZE-002",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 3,
        "name": "Classic Wide Leg Denim",
        "category": "Jeans",
        "price": 1499,
        "match": "96% Style Match",
        "className": "product-blue",
        "colors": ["#6f8fe8", "#232323", "#b9d3ff"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "Wide-leg silhouette in classic blue denim. The kind you wear with everything.",
        "sku": "JNS-WW-WIDE-003",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 4,
        "name": "Sunset Mini Dress",
        "category": "Dresses",
        "price": 1899,
        "match": "92% Style Match",
        "className": "product-orange",
        "colors": ["#ff633d", "#ff3d9a", "#ffd43b"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "A vibrant mini dress blending sunset orange, pink and yellow. Made for golden hours.",
        "sku": "DRS-WW-MINI-004",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 5,
        "name": "Electric Purple Jacket",
        "category": "Jackets",
        "price": 2299,
        "match": "91% Style Match",
        "className": "product-purple",
        "colors": ["#8d6bff", "#1d1d1d", "#ff3d9a"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "A striking electric purple jacket that makes any outfit an event.",
        "sku": "JKT-WW-ELEC-005",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 6,
        "name": "Matcha Everyday Top",
        "category": "Tops",
        "price": 899,
        "match": "88% Style Match",
        "className": "product-green",
        "colors": ["#9ecb72", "#ffffff", "#1d1d1d"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "A muted matcha green top for days when you want effortless and easy.",
        "sku": "TSH-WW-MATCHA-006",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 7,
        "name": "Studio Tailored Oxford Shirt",
        "category": "Shirts",
        "price": 1399,
        "match": "90% Style Match",
        "className": "product-lime",
        "colors": ["#ffffff", "#6f8fe8", "#1d1d1d"],
        "brand": "WEARWISE TAILORED",
        "seller_name": "WEARWISE TAILORED",
        "description": "Crisp button-down Oxford shirt with relaxed collar drape.",
        "sku": "SHR-WW-OXF-007",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 8,
        "name": "Pleated Wide Trousers",
        "category": "Trousers",
        "price": 1799,
        "match": "93% Style Match",
        "className": "product-blue",
        "colors": ["#232323", "#8d6bff", "#9ecb72"],
        "brand": "WEARWISE TAILORED",
        "seller_name": "WEARWISE TAILORED",
        "description": "High-rise tailored pleated trousers with full-length drape.",
        "sku": "TRS-WW-PLEAT-008",
        "try_on_mode": "IMAGE_ONLY",
    },
    {
        "id": 9,
        "name": "A-Line Studio Midi Skirt",
        "category": "Skirts",
        "price": 1599,
        "match": "91% Style Match",
        "className": "product-orange",
        "colors": ["#ff633d", "#1d1d1d", "#ffffff"],
        "brand": "WEARWISE EDIT",
        "seller_name": "WEARWISE EDIT",
        "description": "Structured A-line midi skirt with clean side zip construction.",
        "sku": "SKT-WW-MIDI-009",
        "try_on_mode": "IMAGE_ONLY",
    },
]


def _category_matches(product_category: str, filter_category: str) -> bool:
    fc = filter_category.strip().lower()
    pc = (product_category or "").strip().lower()
    if fc in CATEGORY_ALIASES:
        return pc in CATEGORY_ALIASES[fc]
    return pc == fc


@router.get("/", response_model=list[Product])
def list_products(
    category: str | None = Query(None, description="Filter by category"),
    sort_price: bool = Query(False, description="Sort ascending by price"),
):
    """Return all products, merging published digital garments from MongoDB."""
    pub_by_sku = {p["sku"]: p for p in _list_published_products() if p.get("sku")}
    result: list[dict] = []
    seen_skus: set[str] = set()

    for static_p in PRODUCTS:
        sku = static_p.get("sku")
        if sku and sku in pub_by_sku:
            pub_p = pub_by_sku[sku]
            merged = {
                **static_p,
                **{k: v for k, v in pub_p.items() if v is not None},
                "id": static_p["id"],
                "price": static_p["price"] if sku == "TSH-WW-CREW-001" else pub_p["price"],
                "className": static_p["className"],
            }
            result.append(_enrich_product(merged))
            seen_skus.add(sku)
        else:
            result.append(_enrich_product(static_p))
            if sku:
                seen_skus.add(sku)

    for sku, pub_p in pub_by_sku.items():
        if sku not in seen_skus:
            result.append(_enrich_product(pub_p))

    if category and category != "All":
        result = [p for p in result if _category_matches(p["category"], category)]
    if sort_price:
        result = sorted(result, key=lambda p: p["price"])
    return result


@router.get("/sku/{sku}", response_model=Product)
def get_product_by_sku(sku: str):
    """Resolves a published product by SKU using its active MongoDB catalog publication pointer."""
    static_match = next((p for p in PRODUCTS if p.get("sku") == sku), None)
    if db.is_mongo_active():
        cdb = db.get_db()
        if cdb is not None:
            pub = cdb["catalog_publications"].find_one({"sku": sku, "status": "published"}, {"_id": 0})
            if pub:
                pub_p = _pub_doc_to_product(pub)
                if static_match:
                    merged = {
                        **static_match,
                        **{k: v for k, v in pub_p.items() if v is not None},
                        "id": static_match["id"],
                        "price": static_match["price"] if sku == "TSH-WW-CREW-001" else pub_p["price"],
                        "className": static_match["className"],
                    }
                    return _enrich_product(merged)
                return _enrich_product(pub_p)
    if static_match:
        return _enrich_product(static_match)
    raise HTTPException(status_code=404, detail=f"Published product not found for SKU '{sku}'.")


@router.get("/sku/{sku}/reviews")
def get_product_reviews(sku: str):
    """Returns authentic persisted customer reviews for a SKU (empty list if none exist)."""
    get_product_by_sku(sku)
    rows = db.filter_by("product_reviews", sku=sku)
    rows = sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)
    ratings = [int(r.get("rating", 0)) for r in rows if r.get("rating")]
    avg = round(sum(ratings) / len(ratings), 1) if ratings else None
    return {
        "sku": sku,
        "review_count": len(rows),
        "average_rating": avg,
        "reviews": rows,
    }


@router.post("/sku/{sku}/reviews", status_code=status.HTTP_201_CREATED)
def create_product_review(
    sku: str,
    payload: ReviewCreateRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Persists a genuine shopper review for an existing product SKU."""
    product = get_product_by_sku(sku)
    comment_clean = payload.comment.strip()
    if len(comment_clean) < 3:
        raise HTTPException(status_code=400, detail="Review comment must contain at least 3 characters.")

    auth_user = get_optional_authenticated_user(request, authorization)
    if auth_user and auth_user.get("role") == "seller":
        raise HTTPException(status_code=403, detail="Seller accounts cannot post customer reviews.")
    author = (payload.author_name or (auth_user.get("name") if auth_user else None) or "Verified Shopper").strip()

    verified_purchase = False
    if auth_user:
        user_orders = db.filter_by("orders", user_id=auth_user["id"])
        for ord_doc in user_orders:
            for item in ord_doc.get("items", []):
                if item.get("sku") == sku or item.get("id") == product.get("id"):
                    verified_purchase = True
                    break
            if verified_purchase:
                break

    review_doc = {
        "id": f"rev-{uuid.uuid4().hex[:10]}",
        "sku": sku,
        "product_id": product.get("id"),
        "user_id": auth_user.get("id") if auth_user else None,
        "author_name": author,
        "rating": int(payload.rating),
        "comment": comment_clean,
        "size_purchased": (payload.size_purchased or "").strip() or None,
        "fit_feedback": (payload.fit_feedback or "").strip() or None,
        "verified_purchase": verified_purchase,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("product_reviews", review_doc)
    return review_doc


@router.get("/sku/{sku}/revisions/{revision}/assets/{size}")
def get_published_revision_asset(sku: str, revision: int, size: str):
    """
    Serves the immutable published GLB for a specific SKU, active published revision, and size.
    Rejects drafts, failed/unapproved revisions, stale revisions, and checksum mismatches.
    """
    if not db.is_mongo_active():
        raise HTTPException(status_code=503, detail="Catalog database unavailable.")
    cdb = db.get_db()
    pub = cdb["catalog_publications"].find_one({"sku": sku, "status": "published"}, {"_id": 0})
    if not pub:
        raise HTTPException(status_code=404, detail=f"No published catalog entry for SKU '{sku}'.")
    if int(pub.get("active_revision", -1)) != int(revision):
        raise HTTPException(
            status_code=404,
            detail=f"Revision rev{revision} is not the active published revision for SKU '{sku}'.",
        )
    sz = size.upper()
    sv = (pub.get("size_variants") or {}).get(sz)
    if not sv:
        raise HTTPException(status_code=404, detail=f"Size variant '{sz}' not found for {sku} rev{revision}.")

    asset_path = PUBLISHED_CATALOG_ROOT / sku / f"rev_{revision}" / sv["glb_file"]
    if not asset_path.is_file():
        raise HTTPException(status_code=404, detail=f"Published GLB file missing for {sku} rev{revision} size {sz}.")

    actual_sha = _sha256_file(asset_path)
    expected_sha = sv.get("sha256")
    if expected_sha and actual_sha != expected_sha:
        raise HTTPException(status_code=500, detail="Published asset integrity check failed (SHA-256 mismatch).")

    return FileResponse(
        path=str(asset_path),
        media_type="model/gltf-binary",
        filename=sv["glb_file"],
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": f'"{actual_sha}"',
        },
    )


@router.get("/sku/{sku}/revisions/{revision}/images/{filename}")
def get_published_storefront_image(sku: str, revision: int, filename: str):
    """Serves ONLY storefront-approved imagery for the active published revision (never technical-only images)."""
    if not db.is_mongo_active():
        raise HTTPException(status_code=503, detail="Catalog database unavailable.")
    cdb = db.get_db()
    pub = cdb["catalog_publications"].find_one({"sku": sku, "status": "published"}, {"_id": 0})
    if not pub or int(pub.get("active_revision", -1)) != int(revision):
        raise HTTPException(status_code=404, detail="Published revision not found.")

    allowed = {os.path.basename(im["url"]) for im in (pub.get("storefront_images") or [])}
    safe_name = os.path.basename(filename)
    if safe_name not in allowed:
        raise HTTPException(status_code=403, detail="Image is not approved for public storefront display.")

    img_path = PUBLISHED_CATALOG_ROOT / sku / f"rev_{revision}" / safe_name
    if not img_path.is_file():
        raise HTTPException(status_code=404, detail="Storefront image file missing.")
    ext = img_path.suffix.lower()
    mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return FileResponse(path=str(img_path), media_type=mime, headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if product:
        return get_product_by_sku(product["sku"]) if product.get("sku") else _enrich_product(product)
    pub_match = next((p for p in _list_published_products() if p["id"] == product_id), None)
    if not pub_match:
        raise HTTPException(status_code=404, detail="Product not found")
    return _enrich_product(pub_match)


def resolve_catalog_item(sku: str | None = None, item_id: int | None = None, size: str | None = None) -> dict | None:
    """
    Authoritative catalog lookup for Cart & Order price/variant resolution.
    Checks MongoDB published catalog first, then static PRODUCTS fallback.
    """
    if db.is_mongo_active():
        cdb = db.get_db()
        if cdb is not None:
            pub = None
            if sku:
                pub = cdb["catalog_publications"].find_one({"sku": sku, "status": "published"}, {"_id": 0})
            elif item_id is not None:
                for doc in cdb["catalog_publications"].find({"status": "published"}, {"_id": 0}):
                    if _stable_sku_id(doc["sku"]) == item_id:
                        pub = doc
                        break
            if pub:
                prod = _pub_doc_to_product(pub)
                if size and prod.get("available_sizes") and size.upper() not in [s.upper() for s in prod["available_sizes"]]:
                    raise HTTPException(status_code=400, detail=f"Size '{size}' is not available for SKU '{prod['sku']}'.")
                return prod

    if sku:
        match = next((p for p in PRODUCTS if p.get("sku") == sku), None)
        if match:
            return match
        return None
    if item_id is not None:
        return next((p for p in PRODUCTS if p["id"] == item_id), None)
    return None
