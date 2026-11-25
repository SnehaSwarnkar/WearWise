"""
GET /api/products                                    — list all products (static + published MongoDB catalog)
GET /api/products/sku/{sku}                          — resolve published digital garment product by SKU
GET /api/products/sku/{sku}/revisions/{rev}/assets/{size} — immutable revision-pinned published GLB stream
GET /api/products/sku/{sku}/revisions/{rev}/images/{file} — published storefront-only gallery image
GET /api/products/{id}                               — single product detail
"""

import hashlib
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app import database as db
from app.schemas.products import Product

router = APIRouter(prefix="/api/products", tags=["Products"])

MONOREPO_ROOT = Path(__file__).resolve().parents[3]
PUBLISHED_CATALOG_ROOT = MONOREPO_ROOT / "WEARWISE-BODY-ENGINE" / "artifacts" / "published_catalog"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _stable_sku_id(sku: str) -> int:
    return 1000 + (int(hashlib.sha256(sku.encode("utf-8")).hexdigest()[:6], 16) % 900000)


def _pub_doc_to_product(pub: dict) -> dict:
    sku = pub["sku"]
    storefront_imgs = pub.get("storefront_images") or []
    lead_img = storefront_imgs[0]["url"] if storefront_imgs else None
    return {
        "id": _stable_sku_id(sku),
        "name": pub.get("name", sku),
        "category": pub.get("category", "Tops"),
        "price": int(pub.get("price", 2999)),
        "match": f"96% Verified Fit ({pub.get('published_version', 'v1.0')})",
        "className": "product-pink",
        "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
        "image": lead_img,
        "brand": "WEARWISE EDIT",
        "description": pub.get("description", ""),
        "sku": sku,
        "published_revision": pub.get("active_revision"),
        "published_version": pub.get("published_version"),
        "available_sizes": pub.get("available_sizes", ["S", "M", "L"]),
        "size_variants": pub.get("size_variants"),
        "measurement_chart": pub.get("measurement_chart"),
        "material_profile": pub.get("material_profile"),
        "storefront_images": storefront_imgs,
        "qa_summary": pub.get("qa_summary"),
    }


def _list_published_products() -> list[dict]:
    if not db.is_mongo_active():
        return []
    cdb = db.get_db()
    if cdb is None:
        return []
    docs = list(cdb["catalog_publications"].find({"status": "published"}, {"_id": 0}))
    return [_pub_doc_to_product(d) for d in docs]

# Static product catalogue — mirrors Explore.jsx
PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "Cherry Baby Tee",
        "category": "Tops",
        "price": 799,
        "match": "94% Style Match",
        "className": "product-pink",
        "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
        "brand": "WEARWISE EDIT",
        "description": "A bold, playful baby tee in cherry pink. Perfect for statement-making casual days.",
        "sku": "TSH-WW-CREW-001",
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
        "description": "A relaxed oversized shirt in citrusy lime. Easy to wear, hard to ignore.",
        "sku": "TSH-WW-OVERSIZE-002",
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
        "description": "Wide-leg silhouette in classic blue denim. The kind you wear with everything.",
        "sku": "JNS-WW-WIDE-003",
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
        "description": "A vibrant mini dress blending sunset orange, pink and yellow. Made for golden hours.",
        "sku": "DRS-WW-MINI-004",
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
        "description": "A striking electric purple jacket that makes any outfit an event.",
        "sku": "JKT-WW-ELEC-005",
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
        "description": "A muted matcha green top for days when you want effortless and easy.",
        "sku": "TSH-WW-MATCHA-006",
    },
]


@router.get("/", response_model=list[Product])
def list_products(
    category: str | None = Query(None, description="Filter by category"),
    sort_price: bool = Query(False, description="Sort ascending by price"),
):
    """Return all products, merging published digital garments from MongoDB."""
    result = PRODUCTS[:]
    static_skus = {p.get("sku") for p in result if p.get("sku")}
    for pub_p in _list_published_products():
        if pub_p["sku"] not in static_skus:
            result.append(pub_p)
    if category and category != "All":
        result = [p for p in result if p["category"].lower() == category.lower() or (category == "Tops" and p["category"] == "T-Shirt")]
    if sort_price:
        result = sorted(result, key=lambda p: p["price"])
    return result


@router.get("/sku/{sku}", response_model=Product)
def get_product_by_sku(sku: str):
    """Resolves a published product by SKU using its active MongoDB catalog publication pointer."""
    if db.is_mongo_active():
        cdb = db.get_db()
        if cdb is not None:
            pub = cdb["catalog_publications"].find_one({"sku": sku, "status": "published"}, {"_id": 0})
            if pub:
                return _pub_doc_to_product(pub)
    static_match = next((p for p in PRODUCTS if p.get("sku") == sku), None)
    if static_match:
        return static_match
    raise HTTPException(status_code=404, detail=f"Published product not found for SKU '{sku}'.")


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
    if not product:
        product = next((p for p in _list_published_products() if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


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
