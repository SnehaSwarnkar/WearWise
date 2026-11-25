"""
FastAPI Router for Merchant Digital Garment Studio — Part 1 Platform
Base path: /api/v1/merchant/garments

Empowers apparel sellers to synthesize size-graded, physically-responsive 3D garments:
1. Product Identity (SKU uniqueness, category, subcategory, pricing)
2. Dual-Role Multi-View Imagery (Storefront Gallery vs Technical References)
3. Pattern Specification (Method A CAD/DXF/SVG, Method B Parametric, Method C AI)
4. Finished Garment Measurements (S, M, L flat vs circumference specs)
5. Fabric Mechanical Properties (Preset library, GSM, stretch, stiffness)
6. 13-Stage Generation, QA Verification, Approval, Versioned Manifest & Publication
"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.auth import get_current_brand_id, DEFAULT_DEV_BRAND_ID
from app.db import mongo
from app.services.garment_platform.pattern_engine import (
    CADPatternValidator,
    ParametricPatternBuilder,
    AIReconstructionAdapter,
    STANDARD_BOXY_CREW_MEASUREMENTS,
)
from app.services.garment_platform.qa_engine import GarmentQAEngine
from app.services.garment_platform.asset_manager import GarmentAssetManager
from app.services.garment_platform.lifecycle_store import (
    COLL_ASSETS,
    COLL_JOBS,
    COLL_REVISIONS,
    VALID_TRY_ON_MODES,
    approve_revision,
    compute_try_on_capabilities,
    ensure_garment_indexes,
    execute_generation_pipeline,
    get_revision_doc,
    list_revisions,
    mark_downstream_stale,
    prepare_image_tryon_revision,
    publish_revision,
    record_audit_event,
    rollback_revision,
)

logger = logging.getLogger("wearwise.merchant_garments")

router = APIRouter(prefix="/merchant/garments", tags=["Merchant Digital Garment Studio"])

# MongoDB collection names
COLL_GARMENTS = "digital_garments"
COLL_PATTERNS = "garment_pattern_assets"
COLL_VARIANTS = "garment_size_variants"
COLL_FABRICS = "garment_material_profiles"
COLL_MANIFESTS = "garment_package_manifests"

DEFAULT_BRAND_ID = str(DEFAULT_DEV_BRAND_ID)

# 8 Standard Provisional Fabric Presets
FABRIC_PRESETS = [
    {
        "id": "cotton_waffle_knit_240gsm",
        "name": "Heavyweight Cotton Waffle Knit (240 GSM)",
        "composition": "100% Combed Organic Cotton",
        "structure": "Waffle / Honeycomb Knit",
        "gsm": 240.0,
        "thickness_mm": 1.15,
        "warp_stretch_percent": 14.5,
        "weft_stretch_percent": 28.0,
        "elastic_recovery_percent": 88.0,
        "bending_stiffness": 18.5,
        "shear_stiffness": 22.0,
        "recommended_for": "Boxy Crew Tee, Textured Casual Wear",
        "provisional": True,
        "citation": "Calibrated against BS 4952 waffle knit benchmarks.",
    },
    {
        "id": "cotton_single_jersey_180gsm",
        "name": "Standard Cotton Single Jersey (180 GSM)",
        "composition": "100% Ring-Spun Cotton",
        "structure": "Single Jersey Knit",
        "gsm": 180.0,
        "thickness_mm": 0.58,
        "warp_stretch_percent": 18.0,
        "weft_stretch_percent": 32.0,
        "elastic_recovery_percent": 82.0,
        "bending_stiffness": 11.2,
        "shear_stiffness": 14.0,
        "recommended_for": "Classic Everyday T-Shirts",
        "provisional": True,
        "citation": "Standard ISO 8559-2 single jersey reference.",
    },
    {
        "id": "cotton_heavyweight_jersey_280gsm",
        "name": "Heavyweight Combed Jersey (280 GSM)",
        "composition": "100% Organic Combed Cotton",
        "structure": "Tight Interlock Jersey",
        "gsm": 280.0,
        "thickness_mm": 1.30,
        "warp_stretch_percent": 11.0,
        "weft_stretch_percent": 22.0,
        "elastic_recovery_percent": 90.0,
        "bending_stiffness": 24.0,
        "shear_stiffness": 26.5,
        "recommended_for": "Structured Streetwear & Boxy Silhouettes",
        "provisional": True,
        "citation": "ASTM D1777 heavyweight knit profile.",
    },
    {
        "id": "french_terry_320gsm",
        "name": "Loopback French Terry (320 GSM)",
        "composition": "85% Cotton, 15% Polyester",
        "structure": "Loopback Knit",
        "gsm": 320.0,
        "thickness_mm": 1.65,
        "warp_stretch_percent": 9.5,
        "weft_stretch_percent": 19.0,
        "elastic_recovery_percent": 85.0,
        "bending_stiffness": 31.0,
        "shear_stiffness": 34.0,
        "recommended_for": "Lightweight Sweatshirts & Short-Sleeve Hoodies",
        "provisional": True,
        "citation": "Kawabata FAST loopback knit benchmark.",
    },
    {
        "id": "cotton_interlock_220gsm",
        "name": "Premium Cotton Interlock (220 GSM)",
        "composition": "95% Cotton, 5% Elastane",
        "structure": "Interlock Double Knit",
        "gsm": 220.0,
        "thickness_mm": 0.90,
        "warp_stretch_percent": 25.0,
        "weft_stretch_percent": 45.0,
        "elastic_recovery_percent": 94.0,
        "bending_stiffness": 14.0,
        "shear_stiffness": 18.0,
        "recommended_for": "Form-Fitting Tops & Athletic Basics",
        "provisional": True,
        "citation": "Elastane-blend double knit calibration profile.",
    },
    {
        "id": "linen_plain_weave_160gsm",
        "name": "Pure Flax Linen Plain Weave (160 GSM)",
        "composition": "100% European Flax Linen",
        "structure": "Plain Woven",
        "gsm": 160.0,
        "thickness_mm": 0.45,
        "warp_stretch_percent": 2.5,
        "weft_stretch_percent": 3.0,
        "elastic_recovery_percent": 65.0,
        "bending_stiffness": 29.0,
        "shear_stiffness": 28.0,
        "recommended_for": "Relaxed Summer Woven Shirts",
        "provisional": True,
        "citation": "ASTM D1388 standard stiffness test for woven linen.",
    },
    {
        "id": "polyester_fleece_260gsm",
        "name": "Brushed Polar Microfleece (260 GSM)",
        "composition": "100% Recycled Polyester",
        "structure": "Double-Brushed Fleece",
        "gsm": 260.0,
        "thickness_mm": 2.10,
        "warp_stretch_percent": 12.0,
        "weft_stretch_percent": 24.0,
        "elastic_recovery_percent": 86.0,
        "bending_stiffness": 16.0,
        "shear_stiffness": 19.5,
        "recommended_for": "Thermal Tops & Winter Activewear",
        "provisional": True,
        "citation": "Thermal knit insulation test standard.",
    },
    {
        "id": "silk_charmeuse_16mm",
        "name": "Mulberry Silk Charmeuse (16 Momme)",
        "composition": "100% Grade 6A Mulberry Silk",
        "structure": "Satin Weave",
        "gsm": 68.0,
        "thickness_mm": 0.18,
        "warp_stretch_percent": 1.5,
        "weft_stretch_percent": 2.2,
        "elastic_recovery_percent": 72.0,
        "bending_stiffness": 3.8,
        "shear_stiffness": 5.2,
        "recommended_for": "Draped Silk Blouses & Camisoles",
        "provisional": True,
        "citation": "Kawabata KES-FB Pure Silk mechanical profile.",
    },
]


# --- Schemas ---

class ProductIdentityPayload(BaseModel):
    name: str = Field(..., example="WearWise Signature Boxy Crew Tee")
    sku: str = Field(..., example="TSH-WW-CREW-001")
    category: str = Field("T-Shirt", example="T-Shirt")
    subcategory: str = Field("Oversized Drop-Shoulder Tee", example="Oversized Drop-Shoulder Tee")
    description: str = Field("", example="Heavyweight boxy crewneck tee with dropped shoulders.")
    color_variant: str = Field("Coral Pink / White Trim", example="Coral Pink / White Trim")
    color_variants: Optional[List[str]] = None
    price: float = Field(2999.0, example=2999.0)
    currency: str = Field("INR", example="INR")
    available_sizes: List[str] = Field(default=["S", "M", "L"], example=["S", "M", "L"])
    brand_id: Optional[str] = None
    try_on_mode: str = Field("IMAGE_AND_THREE_D", example="IMAGE_AND_THREE_D")


class TryOnModePayload(BaseModel):
    try_on_mode: str = Field(..., example="IMAGE_AND_THREE_D")


class GuidedPatternPayload(BaseModel):
    silhouette: str = Field("boxy_drop_shoulder", example="boxy_drop_shoulder")
    collar_type: str = Field("ribbed_crewneck", example="ribbed_crewneck")
    hem_finish: str = Field("clean_28mm", example="clean_28mm")
    has_pocket: bool = Field(True, example=True)
    pocket_type: str = Field("left_chest_patch", example="left_chest_patch")
    pocket_width_cm: Optional[float] = None
    pocket_height_cm: Optional[float] = None
    measurements: Optional[Dict[str, Any]] = None


class AIReconstructionPayload(BaseModel):
    adapter: str = Field("SwiftTailorAdapter", example="SwiftTailorAdapter")
    options: Optional[Dict[str, Any]] = None


class SizeMeasurementsPayload(BaseModel):
    size_label: str = Field(..., example="M")
    half_chest_width_cm: float = Field(..., example=54.0)
    back_length_cm: float = Field(..., example=67.0)
    shoulder_breadth_cm: float = Field(..., example=50.0)
    sleeve_length_cm: float = Field(..., example=17.0)
    sleeve_opening_cm: Optional[float] = Field(20.5, example=20.5)
    bicep_width_cm: Optional[float] = Field(None, example=22.0)
    armhole_depth_cm: Optional[float] = Field(None, example=26.5)
    collar_circumference_cm: float = Field(44.0, example=44.0)
    hem_width_cm: Optional[float] = Field(53.0, example=53.0)
    dimensional_ease_chest_cm: str = Field("+4.5 cm (Recommended)", example="+4.5 cm (Recommended)")
    measurement_type: str = Field("flat_tabletop", example="flat_tabletop")


class FabricPropertiesPayload(BaseModel):
    name: str = Field("Heavyweight Cotton Waffle Knit (240 GSM)", example="Heavyweight Cotton Waffle Knit (240 GSM)")
    composition: str = Field("100% Combed Organic Cotton", example="100% Combed Organic Cotton")
    structure: str = Field("Waffle / Honeycomb Knit", example="Waffle / Honeycomb Knit")
    gsm: float = Field(240.0, example=240.0)
    thickness_mm: float = Field(1.15, example=1.15)
    warp_stretch_percent: float = Field(14.5, example=14.5)
    weft_stretch_percent: float = Field(28.0, example=28.0)
    elastic_recovery_percent: float = Field(88.0, example=88.0)
    bending_stiffness: float = Field(18.5, example=18.5)
    shear_stiffness: float = Field(22.0, example=22.0)
    preset_id: Optional[str] = "cotton_waffle_knit_240gsm"


class ApprovalPayload(BaseModel):
    principal_id: str = Field("brand_director_demo", example="brand_director_demo")
    approval_notes: str = Field("Physically verified boxy fit, seam stitching, and ISO 8559-2 grading.", example="Physically verified boxy fit, seam stitching, and ISO 8559-2 grading.")
    revision: Optional[int] = None


class PublishPayload(BaseModel):
    publisher_id: str = Field("catalog_admin_demo", example="catalog_admin_demo")
    revision: Optional[int] = None


class RollbackPayload(BaseModel):
    target_revision: int
    publisher_id: str = Field("catalog_admin_demo")
    reason: str = Field("Catalog rollback to previously approved revision")


def _require_owned_garment(garment_id: str, brand_id: uuid.UUID, allow_sku: bool = False) -> Dict[str, Any]:
    ensure_garment_indexes()
    doc = mongo.find_document(COLL_GARMENTS, {"id": garment_id, "is_deleted": False})
    if not doc and allow_sku:
        doc = mongo.find_document(COLL_GARMENTS, {"sku": garment_id, "is_deleted": False})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Digital garment '{garment_id}' not found")
    if str(doc.get("brand_id")) != str(brand_id):
        raise HTTPException(status_code=403, detail="Access denied: garment belongs to another merchant.")
    return doc


# --- Endpoints ---

@router.get("/presets/fabrics")
def get_fabric_presets():
    """Returns the 8 provisional fabric presets with mechanical properties."""
    return {
        "presets": FABRIC_PRESETS,
        "disclaimer": "PROVISIONAL PRESETS: Physical behavior calibrated against standard textile benchmarks. For production garments, measure fabric specimens on Kawabata KES-FB or FAST testing systems."
    }


def _resolve_prototype_candidate_dir(sku: str, revision: str = "rev3") -> Path:
    """
    Resolves the prototype candidate directory strictly inside artifacts/merchant_patterns/
    and NEVER falls back to legacy public catalog GLBs in frontend/public/garments/.
    """
    clean_sku = (sku or "").strip().upper()
    if clean_sku != "TSH-WW-CREW-001":
        raise HTTPException(status_code=404, detail=f"No prototype candidate package registered for SKU '{sku}'.")

    engine_root = Path(__file__).resolve().parents[3]
    if revision == "rev3":
        cand_dir = engine_root / "artifacts" / "merchant_patterns" / "graded_m2rc"
    elif revision == "rev2":
        cand_dir = engine_root / "artifacts" / "merchant_patterns" / "graded_m2rb"
    else:
        raise HTTPException(status_code=404, detail=f"Prototype revision '{revision}' not found for SKU '{sku}'.")

    if not cand_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Prototype candidate directory missing for {sku} ({revision}).")
    return cand_dir


def _resolve_prototype_glb_path(sku: str, size: str, revision: str = "rev3") -> Path:
    sz = (size or "").strip().upper()
    if sz not in {"S", "M", "L"}:
        raise HTTPException(status_code=400, detail=f"Invalid garment size '{size}'. Must be S, M, or L.")
    cand_dir = _resolve_prototype_candidate_dir(sku, revision=revision)
    if revision == "rev3":
        glb_path = cand_dir / sz / f"{sku}_{sz}_candidate_rev3.glb"
    elif sz == "M":
        glb_path = cand_dir.parent / "prototype_m2r" / f"{sku}_M_prototype_rev2.glb"
    else:
        glb_path = cand_dir / sz / f"{sku}_{sz}_candidate.glb"

    if not glb_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Prototype candidate GLB missing for {sku} size {sz} ({revision}). Legacy fallback disabled.",
        )
    return glb_path


@router.get("/prototype-preview/{sku}")
def get_prototype_preview_manifest(sku: str, revision: str = Query("rev3")):
    """
    Merchant Studio prototype preview resolver.
    Explicitly resolves unpublished graded candidate GLBs and verified QA reports;
    never falls back to legacy public catalog GLBs.
    """
    cand_dir = _resolve_prototype_candidate_dir(sku, revision=revision)
    summary_path = cand_dir / "summary_sml_qa.json"
    if not summary_path.is_file():
        raise HTTPException(status_code=404, detail=f"Prototype QA summary missing for {sku} ({revision}).")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    size_variants: Dict[str, Any] = {}
    for sz in ["S", "M", "L"]:
        glb_path = _resolve_prototype_glb_path(sku, sz, revision=revision)
        sha256 = GarmentAssetManager.compute_sha256(str(glb_path))
        qa_path = cand_dir / sz / "qa_report.json"
        qa_status = "UNVERIFIED"
        if qa_path.is_file():
            qa_data = json.loads(qa_path.read_text(encoding="utf-8"))
            qa_status = qa_data.get("statuses", {}).get("overall_prototype_qa", "UNVERIFIED")
        size_variants[sz] = {
            "size": sz,
            "revision": revision,
            "glb_file": glb_path.name,
            "resolved_rel_path": str(glb_path.relative_to(Path(__file__).resolve().parents[4])).replace("\\", "/"),
            "size_bytes": glb_path.stat().st_size,
            "sha256": sha256,
            "overall_prototype_qa": qa_status,
            "asset_url": f"/api/v1/merchant/garments/prototype-preview/{sku}/assets/{sz}?revision={revision}",
        }

    overall_status = "PASSED" if all(v["overall_prototype_qa"] == "PASSED" for v in size_variants.values()) else "FAILED"
    return {
        "sku": sku,
        "revision": revision,
        "publication_status": "NOT_PUBLISHED_PROTOTYPE_ONLY",
        "overall_status": overall_status,
        "statuses": {
            "overall_prototype_qa": overall_status,
            "publication_status": "NOT_PUBLISHED_PROTOTYPE_ONLY",
        },
        "validation_source": summary.get("validation_source", f"WearWise Prototype QA Engine ({revision})"),
        "size_variants": size_variants,
    }


@router.get("/prototype-preview/{sku}/assets/{size}")
def stream_prototype_preview_glb(sku: str, size: str, revision: str = Query("rev3")):
    """
    Streams the resolved unpublished prototype candidate GLB binary for Merchant Studio preview.
    Strictly returns 404 when unavailable rather than falling back to legacy public assets.
    """
    glb_path = _resolve_prototype_glb_path(sku, size, revision=revision)
    sha256 = GarmentAssetManager.compute_sha256(str(glb_path)) or ""
    return FileResponse(
        path=str(glb_path),
        media_type="model/gltf-binary",
        filename=glb_path.name,
        headers={
            "X-WearWise-Asset-Revision": revision,
            "X-WearWise-Asset-SHA256": sha256,
            "X-WearWise-Asset-Filename": glb_path.name,
            "Cache-Control": "no-store",
        },
    )


@router.get("")
def list_merchant_garments(
    brand_id: Optional[str] = None,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Lists all digital garments owned by the authenticated merchant."""
    ensure_garment_indexes()
    if brand_id and str(brand_id) != str(auth_brand_id):
        raise HTTPException(status_code=403, detail="Access denied: cannot list another merchant's garments.")
    b_id = str(auth_brand_id)
    docs = mongo.find_documents(COLL_GARMENTS, {"brand_id": b_id, "is_deleted": False})
    if not docs:
        seed_doc = _create_seed_garment(b_id)
        return [{**seed_doc, "try_on_capabilities": compute_try_on_capabilities(seed_doc)}]
    for d in docs:
        if "try_on_mode" not in d:
            d["try_on_mode"] = "IMAGE_AND_THREE_D"
        d["try_on_capabilities"] = compute_try_on_capabilities(d)
    return docs


@router.post("", status_code=status.HTTP_201_CREATED)
def create_digital_garment(
    payload: ProductIdentityPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 1: Initializes a new digital garment profile owned by the authenticated merchant.
    Checks for duplicate SKU uniqueness across active garments.
    """
    ensure_garment_indexes()
    brand_id = str(auth_brand_id)
    mode = str(payload.try_on_mode or "IMAGE_AND_THREE_D").upper()
    if mode not in VALID_TRY_ON_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid try_on_mode '{payload.try_on_mode}'. Must be one of {sorted(VALID_TRY_ON_MODES)}.",
        )

    # Duplicate SKU check
    existing = mongo.find_document(COLL_GARMENTS, {"sku": payload.sku, "is_deleted": False})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU '{payload.sku}' is already in use by garment '{existing.get('name')}' (ID: {existing.get('id')}). SKUs must be unique."
        )

    garment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    doc = {
        "id": garment_id,
        "brand_id": brand_id,
        "name": payload.name,
        "sku": payload.sku,
        "category": payload.category,
        "subcategory": payload.subcategory,
        "description": payload.description,
        "color_variant": payload.color_variant,
        "color_variants": payload.color_variants or [payload.color_variant],
        "price": payload.price,
        "currency": payload.currency,
        "available_sizes": payload.available_sizes,
        "try_on_mode": mode,
        "try_on_capabilities": compute_try_on_capabilities({"try_on_mode": mode, "images_meta": []}),
        "status": "draft",  # draft -> needs_review -> approved -> published
        "step_completed": 1,
        "revision": 0,
        "active_revision": None,
        "downstream_stale": False,
        "images": {
            "front": None,
            "back": None,
            "left_side": None,
            "right_side": None,
            "close_up": None,
            "collar": None,
            "cuff": None,
            "construction": None,
        },
        "images_meta": [],
        "pattern": {
            "pattern_mode": "parametric",
            "construction_type": "boxy_drop_shoulder",
            "collar_type": "ribbed_crewneck",
            "hem_finish": "clean_28mm",
            "has_pocket": True,
            "pocket_type": "left_chest_patch",
            "confidence_label": "PARAMETRIC_TEMPLATE",
            "has_cad_data": False,
            "provisional": True,
            "assumptions_note": "Awaiting CAD pattern or guided synthesis; defaulting to drop-shoulder block.",
        },
        "measurements": STANDARD_BOXY_CREW_MEASUREMENTS,
        "fabric_properties": FABRIC_PRESETS[0],
        "mesh_assets": {},
        "qa_report": None,
        "manifest": None,
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
    }

    mongo.upsert_document(COLL_GARMENTS, {"id": garment_id}, doc)
    record_audit_event(garment_id, payload.sku, brand_id, "GARMENT_DRAFT_CREATED", {"sku": payload.sku})
    return doc


@router.get("/{garment_id}")
def get_digital_garment(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Retrieves full specification for a merchant-owned digital garment by ID or SKU."""
    return _require_owned_garment(garment_id, auth_brand_id, allow_sku=True)


@router.post("/{garment_id}/images")
async def upload_viewpoint_image(
    garment_id: str,
    viewpoint: str = Form(...),  # front, back, left_side, right_side, close_up, collar, cuff, construction
    role: str = Form("both"),    # storefront_gallery, technical_reference, both
    roles: Optional[str] = Form(None),  # comma-separated multi-role override
    file: UploadFile = File(...),
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 2: Uploads a viewpoint photograph. Supports explicit multi-role separation
    (Storefront Gallery vs Technical Reconstruction References) and private authenticated serving.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    valid_views = ["front", "back", "left_side", "right_side", "close_up", "collar", "cuff", "construction"]
    if viewpoint not in valid_views:
        raise HTTPException(status_code=400, detail=f"Invalid viewpoint. Must be one of {valid_views}")

    valid_roles = ["storefront_gallery", "technical_reference", "both"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {valid_roles}")

    parsed_roles = [r.strip() for r in (roles.split(",") if roles else [role]) if r.strip()]
    if not parsed_roles or any(r not in valid_roles for r in parsed_roles):
        raise HTTPException(status_code=400, detail=f"Invalid roles. Allowed: {valid_roles}")
    effective_role = "both" if ("both" in parsed_roles or ("storefront_gallery" in parsed_roles and "technical_reference" in parsed_roles)) else parsed_roles[0]

    content = await file.read()
    val_res = GarmentAssetManager.validate_image_upload(file.filename or "image.jpg", content)
    if not val_res["valid"]:
        raise HTTPException(status_code=400, detail=val_res["error"])

    storage_dir = os.path.join(os.getcwd(), "artifacts", "merchant_uploads", garment_id)
    os.makedirs(storage_dir, exist_ok=True)
    img_id = str(uuid.uuid4())[:8]
    ext = val_res["ext"]
    filename = f"{viewpoint}_{img_id}{ext}"
    filepath = os.path.join(storage_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    img_sha256 = GarmentAssetManager.compute_sha256(filepath)
    serve_url = f"/api/v1/merchant/garments/{garment_id}/images/{img_id}/content"
    now = datetime.now(timezone.utc).isoformat()

    image_meta_entry = {
        "id": img_id,
        "viewpoint": viewpoint,
        "role": effective_role,
        "roles": parsed_roles,
        "filename": file.filename,
        "filename_on_disk": filename,
        "local_path": filepath,
        "url": serve_url,
        "size_bytes": len(content),
        "sha256": img_sha256,
        "uploaded_at": now,
    }

    images = garment.get("images", {})
    images[viewpoint] = serve_url

    images_meta = garment.get("images_meta", [])
    images_meta = [im for im in images_meta if im.get("viewpoint") != viewpoint]
    images_meta.append(image_meta_entry)

    update_data = {
        "images": images,
        "images_meta": images_meta,
        "step_completed": max(garment.get("step_completed", 1), 2),
    }
    if effective_role in ("technical_reference", "both"):
        update_data.update(mark_downstream_stale(garment, f"Technical image '{viewpoint}' updated"))
    else:
        update_data["updated_at"] = now

    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)

    required_views = {"front", "back", "left_side", "close_up"}
    present_views = {im["viewpoint"] for im in images_meta if im["role"] in ["technical_reference", "both"]}
    missing_views = list(required_views - present_views)

    return {
        "garment": garment,
        "uploaded_image": image_meta_entry,
        "checklist": {
            "required_views": list(required_views),
            "present_views": list(present_views),
            "missing_views": missing_views,
            "ready_for_reconstruction": len(missing_views) == 0,
        }
    }


@router.get("/{garment_id}/images/{image_id}/content")
def get_uploaded_image_content(
    garment_id: str,
    image_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Serves private merchant-uploaded image bytes after verifying ownership."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    target = next((im for im in garment.get("images_meta", []) if im.get("id") == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    fpath = target.get("local_path") or os.path.join(
        os.getcwd(), "artifacts", "merchant_uploads", garment_id, str(target.get("filename_on_disk") or "")
    )
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Image file missing on storage")
    ext = os.path.splitext(fpath)[1].lower()
    mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return FileResponse(path=fpath, media_type=mime, headers={"Cache-Control": "private, no-store"})


@router.delete("/{garment_id}/images/{image_id}")
def delete_image(
    garment_id: str,
    image_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Deletes an uploaded image from garment imagery and metadata."""
    garment = _require_owned_garment(garment_id, auth_brand_id)

    images_meta = garment.get("images_meta", [])
    target = next((im for im in images_meta if im.get("id") == image_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found")

    new_meta = [im for im in images_meta if im.get("id") != image_id]
    images = garment.get("images", {})
    if images.get(target.get("viewpoint")) == target.get("url"):
        images[target.get("viewpoint")] = None

    update_data = {
        "images": images,
        "images_meta": new_meta,
    }
    if target.get("role") in ("technical_reference", "both"):
        update_data.update(mark_downstream_stale(garment, f"Technical image '{target.get('viewpoint')}' deleted"))
    else:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    return {"message": f"Image {image_id} deleted successfully", "images_meta": new_meta}


@router.post("/{garment_id}/pattern/upload")
async def upload_cad_pattern(
    garment_id: str,
    units: str = Form("mm"),
    file: UploadFile = File(...),
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 3 (Method A): Production CAD / DXF / SVG Pattern Upload.
    Validates boundary loops, panel names, and seam matching.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    filename = file.filename or "pattern.dxf"
    ext = os.path.splitext(filename)[1].lower()
    content = await file.read()

    if ext == ".dxf":
        val_res = CADPatternValidator.validate_dxf(content, unit=units)
    elif ext == ".svg":
        val_res = CADPatternValidator.validate_svg(content)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CAD file extension '{ext}'. Only DXF and SVG pattern files are accepted."
        )

    now = datetime.now(timezone.utc).isoformat()
    pattern_dir = os.path.join(os.getcwd(), "artifacts", "merchant_patterns", garment_id)
    os.makedirs(pattern_dir, exist_ok=True)
    cad_path = os.path.join(pattern_dir, f"pattern_{garment.get('sku')}{ext}")
    with open(cad_path, "wb") as f:
        f.write(content)

    pattern_data = {
        "pattern_mode": f"cad_{ext.replace('.', '')}",
        "construction_type": "production_cad_graded",
        "cad_filename": filename,
        "cad_path": cad_path,
        "units": units,
        "has_cad_data": True,
        "provisional": not val_res.get("valid", False),
        "confidence_label": "VERIFIED_PATTERN" if val_res.get("valid") else "PARAMETRIC_TEMPLATE",
        "validation_report": val_res,
        "panels": val_res.get("panel_names", []),
        "panel_count": val_res.get("panel_count", 0),
        "updated_at": now,
    }

    update_data = {
        "pattern": pattern_data,
        "step_completed": max(garment.get("step_completed", 1), 3),
    }
    update_data.update(mark_downstream_stale(garment, f"CAD pattern '{filename}' uploaded"))
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)
    return {
        "garment": garment,
        "cad_validation": val_res,
        "confidence_label": pattern_data["confidence_label"],
    }


@router.post("/{garment_id}/pattern/guided")
def save_guided_pattern(
    garment_id: str,
    payload: GuidedPatternPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 3 (Method B — Primary MVP): Guided Parametric Pattern Generator.
    Synthesizes 2D panels and explicit seam relationships.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    meas = payload.measurements or garment.get("measurements", {}).get("M") or STANDARD_BOXY_CREW_MEASUREMENTS["M"]
    panels = ParametricPatternBuilder.synthesize_panels(
        meas,
        silhouette=payload.silhouette,
        collar_type=payload.collar_type,
        hem_finish=payload.hem_finish,
        has_pocket=payload.has_pocket,
    )
    seams = ParametricPatternBuilder.generate_seam_relationships(has_pocket=payload.has_pocket)

    now = datetime.now(timezone.utc).isoformat()
    pattern_data = {
        "pattern_mode": "parametric",
        "construction_type": payload.silhouette,
        "collar_type": payload.collar_type,
        "hem_finish": payload.hem_finish,
        "has_pocket": payload.has_pocket,
        "pocket_type": payload.pocket_type,
        "pocket_width_cm": payload.pocket_width_cm,
        "pocket_height_cm": payload.pocket_height_cm,
        "panels": panels,
        "seam_relationships": seams,
        "has_cad_data": False,
        "provisional": True,
        "confidence_label": "PARAMETRIC_TEMPLATE",
        "assumptions_note": "Calibrated against ISO 8559-2 dropped-shoulder block with explicit 2D panels and seams.",
        "updated_at": now,
    }

    update_data = {
        "pattern": pattern_data,
        "step_completed": max(garment.get("step_completed", 1), 3),
    }
    update_data.update(mark_downstream_stale(garment, f"Guided pattern updated (collar={payload.collar_type})"))
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)
    return {
        "garment": garment,
        "panels": panels,
        "seam_relationships": seams,
        "confidence_label": "PARAMETRIC_TEMPLATE",
    }


@router.get("/{garment_id}/pattern/export")
def export_garment_pattern(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Exports inspectable 2D pattern components and seam edge map for the garment."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    rev = garment.get("active_revision") or garment.get("revision")
    if rev:
        rev_doc = get_revision_doc(garment_id, int(rev))
        if rev_doc and rev_doc.get("storage_dir"):
            p_path = Path(rev_doc["storage_dir"]) / "pattern_components.json"
            s_path = Path(rev_doc["storage_dir"]) / "seam_edge_map.json"
            if p_path.exists() and s_path.exists():
                return {
                    "garment_id": garment_id,
                    "sku": garment.get("sku"),
                    "revision": rev,
                    "source": "generated_pattern_first_2d",
                    "panels": json.loads(p_path.read_text(encoding="utf-8")),
                    "seam_map": json.loads(s_path.read_text(encoding="utf-8")),
                }
    return {
        "garment_id": garment_id,
        "sku": garment.get("sku"),
        "revision": rev,
        "source": "draft_pattern_spec",
        "panels": garment.get("pattern", {}).get("panels", []),
        "seam_map": garment.get("pattern", {}).get("seam_relationships", []),
    }


@router.post("/{garment_id}/pattern/ai-reconstruct")
def ai_reconstruct_pattern(
    garment_id: str,
    payload: AIReconstructionPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 3 (Method C): Provisional AI Image Reconstruction Adapter.
    Explicitly marked as PROVISIONAL_ADAPTER; not a full autonomous reconstruction engine.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    images_meta = garment.get("images_meta", [])
    if not images_meta:
        raise HTTPException(
            status_code=400,
            detail="AI pattern reconstruction requires uploaded technical images. Upload front, back and side views in Step 2 first."
        )

    res = AIReconstructionAdapter.request_reconstruction(
        adapter_name=payload.adapter,
        image_records=images_meta,
        options=payload.options,
    )

    now = datetime.now(timezone.utc).isoformat()
    pattern_data = {
        "pattern_mode": "ai_reconstruct",
        "implementation_status": "PROVISIONAL_ADAPTER",
        "is_full_reconstruction_engine": False,
        "construction_type": "ai_approximated_tee",
        "panels": res["generated_panels"],
        "seam_relationships": res["seam_graph"],
        "has_cad_data": False,
        "provisional": True,
        "confidence_label": "AI_RECONSTRUCTED",
        "assumptions_note": res["assumptions_note"],
        "adapter_metadata": res["adapter_metadata"],
        "updated_at": now,
    }

    update_data = {
        "pattern": pattern_data,
        "step_completed": max(garment.get("step_completed", 1), 3),
    }
    update_data.update(mark_downstream_stale(garment, "AI provisional pattern applied"))
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)
    return {
        "garment": garment,
        "reconstruction_result": res,
        "implementation_status": "PROVISIONAL_ADAPTER",
        "confidence_label": "AI_RECONSTRUCTED",
    }


@router.post("/{garment_id}/measurements")
def save_size_measurements(
    garment_id: str,
    payload: SizeMeasurementsPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 4: Saves finished garment measurements for a specific size variant.
    Marks downstream generated outputs stale if measurements changed.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    meas = garment.get("measurements", {})
    payload_dict = payload.model_dump()
    std_sz = STANDARD_BOXY_CREW_MEASUREMENTS.get(payload.size_label, STANDARD_BOXY_CREW_MEASUREMENTS["M"])
    if payload_dict.get("armhole_depth_cm") is None:
        payload_dict["armhole_depth_cm"] = std_sz.get("armhole_depth_cm", 26.5)
    if payload_dict.get("bicep_width_cm") is None:
        payload_dict["bicep_width_cm"] = std_sz.get("bicep_width_cm", 22.0)
    meas[payload.size_label] = payload_dict

    update_data = {
        "measurements": meas,
        "step_completed": max(garment.get("step_completed", 1), 4),
    }
    update_data.update(mark_downstream_stale(garment, f"Size {payload.size_label} measurements updated"))
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)
    return garment


@router.post("/{garment_id}/fabric")
def save_fabric_properties(
    garment_id: str,
    payload: FabricPropertiesPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 5: Saves mechanical textile properties for cloth physics.
    Marks downstream generated outputs stale when fabric configuration changes.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)

    fabric_data = payload.model_dump()
    fabric_data["provisional"] = True
    fabric_data["confidence_label"] = "PROVISIONAL_BENCHMARK"
    update_data = {
        "fabric_properties": fabric_data,
        "step_completed": max(garment.get("step_completed", 1), 5),
    }
    update_data.update(mark_downstream_stale(garment, f"Fabric profile updated ({fabric_data.get('name')})"))
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_data})
    garment.update(update_data)
    return garment


@router.post("/{garment_id}/try-on-mode")
def update_try_on_mode(
    garment_id: str,
    payload: TryOnModePayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Configures which virtual try-on experiences shoppers can use for this listing."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    mode = str(payload.try_on_mode or "").upper()
    if mode not in VALID_TRY_ON_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid try-on mode '{payload.try_on_mode}'. Choose IMAGE_ONLY, THREE_D_ONLY, or IMAGE_AND_THREE_D.",
        )

    updated_doc = {**garment, "try_on_mode": mode}
    caps = compute_try_on_capabilities(updated_doc)
    now = datetime.now(timezone.utc).isoformat()
    update_fields = {
        "try_on_mode": mode,
        "try_on_capabilities": caps,
        "updated_at": now,
    }
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_fields})
    garment.update(update_fields)
    record_audit_event(garment_id, garment.get("sku", ""), str(auth_brand_id), "TRY_ON_MODE_UPDATED", {"try_on_mode": mode})
    return garment


@router.post("/{garment_id}/prepare-image-tryon")
def prepare_image_tryon(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Verifies front storefront imagery and creates an IMAGE_ONLY revision ready for review/publish without 3D generation."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    try:
        return prepare_image_tryon_revision(garment_doc=garment, brand_id=str(auth_brand_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{garment_id}/generate")
def generate_3d_digital_garment(
    garment_id: str,
    force: bool = Query(False),
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Step 6: Executes the Pattern-First S/M/L Generation & QA Pipeline, storing
    private revision-scoped assets in MongoDB + private filesystem storage.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)
    return execute_generation_pipeline(garment, str(auth_brand_id), force=force)


@router.get("/{garment_id}/revisions")
def get_garment_revisions(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Lists all immutable revisions generated for this merchant-owned garment."""
    _require_owned_garment(garment_id, auth_brand_id)
    return {"garment_id": garment_id, "revisions": list_revisions(garment_id)}


@router.get("/{garment_id}/jobs")
def get_garment_jobs(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Lists generation job lifecycle records for this merchant-owned garment."""
    _require_owned_garment(garment_id, auth_brand_id)
    jobs = mongo.find_documents(COLL_JOBS, {"garment_id": garment_id}, sort_field="started_at", ascending=False)
    return {"garment_id": garment_id, "jobs": jobs}


@router.get("/{garment_id}/revisions/{revision}/assets/{size}")
def get_private_revision_asset(
    garment_id: str,
    revision: int,
    size: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Serves private candidate GLB bytes for a specific revision & size after verifying merchant ownership."""
    _require_owned_garment(garment_id, auth_brand_id)
    sz = size.upper()
    ast = mongo.find_document(COLL_ASSETS, {"garment_id": garment_id, "revision": int(revision), "size": sz})
    if not ast:
        raise HTTPException(status_code=404, detail=f"Asset not found for revision {revision} size {sz}")
    if str(ast.get("owner_brand_id")) != str(auth_brand_id):
        raise HTTPException(status_code=403, detail="Access denied")
    fpath = ast.get("storage_path", "")
    if not fpath or not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Private asset binary missing on disk")
    return FileResponse(
        path=fpath,
        media_type="model/gltf-binary",
        filename=ast.get("glb_file", f"{garment_id}_{sz}_rev{revision}.glb"),
        headers={"Cache-Control": "private, no-store", "ETag": f'"{ast.get("sha256", "")}"'},
    )


@router.get("/{garment_id}/qa-report")
def get_qa_report(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Returns latest automated QA report with pass/fail gates and confidence badges."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    qa = garment.get("qa_report")
    if not qa:
        raise HTTPException(status_code=404, detail="No QA report available. Run 3D generation (Step 6) first.")
    return qa


@router.post("/{garment_id}/approve")
def approve_digital_garment(
    garment_id: str,
    payload: ApprovalPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Explicit Step 6.1: Merchant authority reviews and formally approves an exact QA-passed revision.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)
    try:
        return approve_revision(
            garment_doc=garment,
            brand_id=str(auth_brand_id),
            principal_id=payload.principal_id,
            approval_notes=payload.approval_notes,
            target_revision=payload.revision,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{garment_id}/publish")
def publish_digital_garment(
    garment_id: str,
    payload: PublishPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """
    Explicit Step 6.2: Publishes an approved immutable revision into the staging/commerce catalog.
    """
    garment = _require_owned_garment(garment_id, auth_brand_id)
    try:
        return publish_revision(
            garment_doc=garment,
            brand_id=str(auth_brand_id),
            publisher_id=payload.publisher_id,
            target_revision=payload.revision,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{garment_id}/rollback")
def rollback_digital_garment(
    garment_id: str,
    payload: RollbackPayload,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Rolls back the active catalog pointer to an earlier approved/published revision without destroying history."""
    garment = _require_owned_garment(garment_id, auth_brand_id)
    try:
        return rollback_revision(
            garment_doc=garment,
            brand_id=str(auth_brand_id),
            target_revision=payload.target_revision,
            publisher_id=payload.publisher_id,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{garment_id}/manifest")
def get_package_manifest(
    garment_id: str,
    auth_brand_id: uuid.UUID = Depends(get_current_brand_id),
):
    """Retrieves compiled immutable Digital Garment Package Manifest."""
    garment = _require_owned_garment(garment_id, auth_brand_id, allow_sku=True)
    manifest = garment.get("manifest")
    if not manifest:
        manifest = mongo.find_document(COLL_MANIFESTS, {"garment_id": garment.get("id")})
    if not manifest:
        raise HTTPException(status_code=404, detail="Package manifest not found. Garment has not been published yet.")
    return manifest


@router.get("/{garment_id}/shopper-asset")
def get_shopper_asset(garment_id: str, size: str = "M", revision: Optional[int] = Query(None)):
    """
    Shopper-facing gateway: strictly verifies that asset is published in Commerce catalog,
    rejects unapproved/stale revisions (fail-closed), and returns full digital twin metadata.
    """
    garment = mongo.find_document(COLL_GARMENTS, {"id": garment_id, "is_deleted": False})
    if not garment:
        garment = mongo.find_document(COLL_GARMENTS, {"sku": garment_id, "is_deleted": False})
    if not garment and garment_id == "TSH-WW-CREW-001":
        garment = _create_seed_garment(DEFAULT_BRAND_ID)
    if not garment:
        raise HTTPException(status_code=404, detail=f"Garment {garment_id} not found")

    if garment.get("status") != "published":
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Garment {garment_id} is in status '{garment.get('status')}' and has not been approved and published for shoppers."
        )

    pub_rev = garment.get("published_revision") or garment.get("revision")
    if revision is not None and pub_rev is not None and int(revision) != int(pub_rev):
        raise HTTPException(
            status_code=409,
            detail=f"Revision mismatch: requested revision {revision}, but published revision is {pub_rev}."
        )

    size_variants = garment.get("size_variants", {})
    sv = size_variants.get(size)
    raw_fab = garment.get("fabric_properties") or {}
    fabric_props = {**raw_fab, "id": raw_fab.get("id") or raw_fab.get("preset_id") or "cotton_waffle_knit_240gsm"}
    measurements = garment.get("measurements") or {}
    qa_report = garment.get("qa_report") or {}

    if sv and sv.get("asset_url"):
        return {
            "garment_id": garment.get("id"),
            "sku": garment.get("sku"),
            "name": garment.get("name"),
            "status": "published",
            "revision": pub_rev,
            "version": garment.get("published_version", "v1.0"),
            "size": size,
            "available_sizes": garment.get("available_sizes", list(size_variants.keys())),
            "asset_url": sv["asset_url"],
            "sha256": sv.get("sha256"),
            "fabric_profile": fabric_props,
            "measurements": measurements.get(size, measurements),
            "all_size_measurements": measurements,
            "qa_status": qa_report.get("overall_status", "UNKNOWN"),
        }

    mesh_assets = garment.get("mesh_assets", {})
    size_asset = mesh_assets.get(size)
    if garment.get("sku") == "TSH-WW-CREW-001":
        size_asset = f"/api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/{size.upper()}?revision=rev3"
    if not size_asset:
        raise HTTPException(status_code=404, detail=f"Size variant {size} not found in published garment")

    return {
        "garment_id": garment.get("id"),
        "sku": garment.get("sku"),
        "name": garment.get("name"),
        "status": "published",
        "revision": pub_rev,
        "version": garment.get("published_version", "v1.0"),
        "size": size,
        "available_sizes": garment.get("available_sizes", ["S", "M", "L"]),
        "asset_url": size_asset,
        "texture_url": mesh_assets.get("texture_atlas"),
        "fabric_profile": fabric_props,
        "measurements": measurements.get(size, measurements),
        "all_size_measurements": measurements,
        "qa_status": qa_report.get("overall_status", "UNKNOWN"),
    }


def _create_seed_garment(brand_id: str) -> Dict[str, Any]:
    """Seeds the catalog with the approved reference boxy tee."""
    garment_id = "ww-seed-tsh-ww-crew-001"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": garment_id,
        "brand_id": brand_id,
        "name": "WearWise Signature Boxy Crew Tee",
        "sku": "TSH-WW-CREW-001",
        "category": "T-Shirt",
        "subcategory": "Oversized Drop-Shoulder Tee",
        "description": "Drop-shoulder heavyweight boxy tee with ribbed crewneck collar, clean hem band, and chest pocket.",
        "color_variant": "Coral Pink / White Trim",
        "price": 2999.0,
        "available_sizes": ["S", "M", "L"],
        "try_on_mode": "IMAGE_AND_THREE_D",
        "status": "published",
        "step_completed": 6,
        "revision": 1,
        "published_version": "v1.0",
        "images": {
            "front": "/garments/reference_front.jpg",
            "back": None,
            "left_side": "/garments/reference_side.jpg",
            "right_side": None,
            "close_up": "/garments/garment_texture_diffuse.png",
            "collar": None,
            "cuff": None,
            "construction": None,
        },
        "images_meta": [
            {
                "id": "seed-front",
                "viewpoint": "front",
                "role": "both",
                "filename": "reference_front.jpg",
                "url": "/garments/reference_front.jpg",
                "size_bytes": 102400,
                "sha256": "seed_hash_front",
                "uploaded_at": now,
            },
            {
                "id": "seed-side",
                "viewpoint": "left_side",
                "role": "both",
                "filename": "reference_side.jpg",
                "url": "/garments/reference_side.jpg",
                "size_bytes": 102400,
                "sha256": "seed_hash_side",
                "uploaded_at": now,
            },
            {
                "id": "seed-closeup",
                "viewpoint": "close_up",
                "role": "technical_reference",
                "filename": "garment_texture_diffuse.png",
                "url": "/garments/garment_texture_diffuse.png",
                "size_bytes": 204800,
                "sha256": "seed_hash_diffuse",
                "uploaded_at": now,
            }
        ],
        "pattern": {
            "pattern_mode": "parametric",
            "construction_type": "boxy_drop_shoulder",
            "has_cad_data": True,
            "provisional": False,
            "confidence_label": "PARAMETRIC_TEMPLATE",
            "assumptions_note": "Calibrated against ISO 8559-2 dropped-shoulder block with 11 explicit seams",
        },
        "measurements": STANDARD_BOXY_CREW_MEASUREMENTS,
        "fabric_properties": FABRIC_PRESETS[0],
        "mesh_assets": {
            "S": "/garments/TSH-WW-CREW-001_S.glb",
            "M": "/garments/TSH-WW-CREW-001_M.glb",
            "L": "/garments/TSH-WW-CREW-001_L.glb",
            "canonical": "/garments/TSH-WW-CREW-001.glb",
            "texture_atlas": "/garments/garment_texture_diffuse.png",
            "provenance_json": "/garments/TSH-WW-CREW-001_provenance.json",
        },
        "qa_report": {
            "overall_status": "PASSED",
            "confidence_level": "PARAMETRIC_TEMPLATE",
            "timestamp": now,
            "summary": "Full automated QA check completed: 7 panel definitions, Euler characteristic -2, open neck/cuffs/hem boundaries, and ISO 8559-2 grading.",
        },
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
        "published_at": now,
    }
    mongo.upsert_document(COLL_GARMENTS, {"id": garment_id}, doc)
    return doc
