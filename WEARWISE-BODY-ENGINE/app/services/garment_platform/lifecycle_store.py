"""
WearWise Digital Garment Platform — MongoDB Lifecycle, Versioning & Publication Store
===================================================================================
Manages immutable revisions, generation job state transitions, private/published
asset metadata, SHA-256 verification, seller ownership checks, and atomic
commerce catalog publication/rollback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymongo

from app.db import mongo
from app.services.garment_platform.asset_manager import GarmentAssetManager
from app.services.garment_platform.pattern_engine import (
    ParametricPatternBuilder,
    STANDARD_BOXY_CREW_MEASUREMENTS,
)
from app.services.garment_platform.qa_engine import GarmentQAEngine

logger = logging.getLogger("wearwise.garment_platform.lifecycle")

COLL_GARMENTS = "digital_garments"
COLL_REVISIONS = "garment_revisions"
COLL_JOBS = "garment_generation_jobs"
COLL_ASSETS = "garment_assets"
COLL_QA_REPORTS = "garment_qa_reports"
COLL_MANIFESTS = "garment_package_manifests"
COLL_APPROVALS = "garment_approval_events"
COLL_PUBLICATIONS = "garment_publications"
COLL_AUDIT_EVENTS = "garment_audit_events"
COLL_COMMERCE_PUBLICATIONS = "catalog_publications"

VALID_TRY_ON_MODES = {"IMAGE_ONLY", "THREE_D_ONLY", "IMAGE_AND_THREE_D"}


def has_storefront_front_photo(garment_doc: Dict[str, Any]) -> bool:
    for im in garment_doc.get("images_meta", []):
        roles = im.get("roles") or [im.get("role")]
        if im.get("viewpoint") == "front" and any(r in ("storefront_gallery", "both") for r in roles):
            return True
    return False


def has_any_storefront_photo(garment_doc: Dict[str, Any]) -> bool:
    for im in garment_doc.get("images_meta", []):
        roles = im.get("roles") or [im.get("role")]
        if any(r in ("storefront_gallery", "both") for r in roles):
            return True
    return False


def compute_try_on_capabilities(
    garment_doc: Dict[str, Any],
    size_variants: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    raw_mode = str(garment_doc.get("try_on_mode") or "IMAGE_AND_THREE_D").upper()
    mode = raw_mode if raw_mode in VALID_TRY_ON_MODES else "IMAGE_AND_THREE_D"
    sv = size_variants if size_variants is not None else (garment_doc.get("size_variants") or garment_doc.get("mesh_assets") or {})
    has_3d = bool(sv) and any(
        isinstance(v, dict) and bool(v.get("asset_url")) or isinstance(v, str)
        for k, v in sv.items()
        if k in ("S", "M", "L", "XS", "XL")
    )
    has_photos = has_any_storefront_photo(garment_doc)
    image_req = mode in ("IMAGE_ONLY", "IMAGE_AND_THREE_D")
    three_d_req = mode in ("THREE_D_ONLY", "IMAGE_AND_THREE_D")
    return {
        "mode": mode,
        "imageTryOnEnabled": image_req and has_photos,
        "threeDTryOnEnabled": three_d_req and has_3d,
        "imageTryOnReady": image_req and has_photos,
        "threeDTryOnReady": three_d_req and has_3d,
        "imageDisabledReason": (
            None
            if not image_req
            else (None if has_photos else "Upload a front storefront photo before enabling Image Try-On.")
        )
        if image_req
        else "The seller configured this item exclusively for Interactive 3D Try-On.",
        "threeDDisabledReason": (
            None
            if three_d_req and has_3d
            else (
                "The seller has not enabled Interactive 3D Try-On for this item."
                if not three_d_req
                else "3D garment model assets have not been generated and approved yet."
            )
        ),
    }

BODY_ENGINE_ROOT = Path(__file__).resolve().parents[3]
PRIVATE_STORAGE_ROOT = BODY_ENGINE_ROOT / "artifacts" / "merchant_private"
PUBLISHED_CATALOG_ROOT = BODY_ENGINE_ROOT / "artifacts" / "published_catalog"

_indexes_initialized = False
_publish_lock = threading.Lock()


def ensure_garment_indexes() -> None:
    """Safely creates required MongoDB indexes across Body Engine and Commerce staging/prod DBs."""
    global _indexes_initialized
    if _indexes_initialized or not mongo.is_active():
        return
    try:
        g_col = mongo.get_collection(COLL_GARMENTS)
        if g_col is not None:
            g_col.create_index([("id", pymongo.ASCENDING)], unique=True, name="idx_garment_id_unique")
            g_col.create_index(
                [("sku", pymongo.ASCENDING)],
                unique=True,
                partialFilterExpression={"is_deleted": False},
                name="idx_garment_active_sku_unique",
            )
            g_col.create_index([("brand_id", pymongo.ASCENDING), ("is_deleted", pymongo.ASCENDING)], name="idx_garment_owner")

        r_col = mongo.get_collection(COLL_REVISIONS)
        if r_col is not None:
            r_col.create_index([("garment_id", pymongo.ASCENDING), ("revision", pymongo.ASCENDING)], unique=True, name="idx_rev_garment_rev_unique")
            r_col.create_index([("sku", pymongo.ASCENDING), ("revision", pymongo.DESCENDING)], name="idx_rev_sku")
            r_col.create_index([("brand_id", pymongo.ASCENDING), ("status", pymongo.ASCENDING)], name="idx_rev_owner_status")

        j_col = mongo.get_collection(COLL_JOBS)
        if j_col is not None:
            j_col.create_index([("job_id", pymongo.ASCENDING)], unique=True, name="idx_job_id_unique")
            j_col.create_index([("garment_id", pymongo.ASCENDING), ("input_hash", pymongo.ASCENDING)], name="idx_job_idempotency")

        a_col = mongo.get_collection(COLL_ASSETS)
        if a_col is not None:
            a_col.create_index([("asset_id", pymongo.ASCENDING)], unique=True, name="idx_asset_id_unique")
            a_col.create_index([("garment_id", pymongo.ASCENDING), ("revision", pymongo.ASCENDING), ("size", pymongo.ASCENDING)], name="idx_asset_lookup")
            a_col.create_index([("owner_brand_id", pymongo.ASCENDING), ("access_classification", pymongo.ASCENDING)], name="idx_asset_owner_acl")

        q_col = mongo.get_collection(COLL_QA_REPORTS)
        if q_col is not None:
            q_col.create_index([("qa_id", pymongo.ASCENDING)], unique=True, name="idx_qa_id_unique")
            q_col.create_index([("garment_id", pymongo.ASCENDING), ("revision", pymongo.ASCENDING)], name="idx_qa_garment_rev")

        ap_col = mongo.get_collection(COLL_APPROVALS)
        if ap_col is not None:
            ap_col.create_index([("approval_id", pymongo.ASCENDING)], unique=True, name="idx_approval_id_unique")
            ap_col.create_index([("garment_id", pymongo.ASCENDING), ("revision", pymongo.ASCENDING)], name="idx_approval_garment_rev")

        p_col = mongo.get_collection(COLL_PUBLICATIONS)
        if p_col is not None:
            p_col.create_index([("publication_id", pymongo.ASCENDING)], unique=True, name="idx_pub_id_unique")
            p_col.create_index([("sku", pymongo.ASCENDING), ("revision", pymongo.DESCENDING)], name="idx_pub_sku_rev")

        au_col = mongo.get_collection(COLL_AUDIT_EVENTS)
        if au_col is not None:
            au_col.create_index([("garment_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)], name="idx_audit_garment_time")

        cp_col = mongo.get_commerce_collection(COLL_COMMERCE_PUBLICATIONS)
        if cp_col is not None:
            cp_col.create_index([("sku", pymongo.ASCENDING)], unique=True, name="idx_catalog_pub_sku_unique")
            cp_col.create_index([("active_revision", pymongo.ASCENDING), ("status", pymongo.ASCENDING)], name="idx_catalog_pub_rev_status")

        _indexes_initialized = True
    except Exception as exc:
        logger.warning(f"MongoDB index initialization warning: {exc}")


def record_audit_event(garment_id: str, sku: str, brand_id: str, event_type: str, details: Dict[str, Any]) -> None:
    ensure_garment_indexes()
    mongo.upsert_document(
        COLL_AUDIT_EVENTS,
        {"event_id": str(uuid.uuid4())},
        {
            "event_id": str(uuid.uuid4()),
            "garment_id": garment_id,
            "sku": sku,
            "brand_id": brand_id,
            "event_type": event_type,
            "details": details,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def compute_generation_input_hash(garment_doc: Dict[str, Any]) -> str:
    """Deterministic SHA-256 of all inputs that affect 3D garment generation."""
    tech_images = [
        {"viewpoint": im.get("viewpoint"), "sha256": im.get("sha256"), "roles": im.get("roles", [im.get("role")])}
        for im in garment_doc.get("images_meta", [])
        if im.get("role") in ("technical_reference", "both")
        or any(r in ("technical_reference", "both") for r in im.get("roles", []))
    ]
    payload = {
        "sku": garment_doc.get("sku"),
        "available_sizes": garment_doc.get("available_sizes", ["S", "M", "L"]),
        "pattern": {
            "pattern_mode": garment_doc.get("pattern", {}).get("pattern_mode"),
            "construction_type": garment_doc.get("pattern", {}).get("construction_type"),
            "collar_type": garment_doc.get("pattern", {}).get("collar_type"),
            "hem_finish": garment_doc.get("pattern", {}).get("hem_finish"),
            "has_pocket": garment_doc.get("pattern", {}).get("has_pocket", True),
            "pocket_width_cm": garment_doc.get("pattern", {}).get("pocket_width_cm"),
            "pocket_height_cm": garment_doc.get("pattern", {}).get("pocket_height_cm"),
            "cad_path": garment_doc.get("pattern", {}).get("cad_path"),
        },
        "measurements": garment_doc.get("measurements", {}),
        "fabric_properties": garment_doc.get("fabric_properties", {}),
        "technical_images": sorted(tech_images, key=lambda x: str(x.get("viewpoint"))),
    }
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def mark_downstream_stale(garment_doc: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """
    Invalidates downstream draft QA/assets when merchant inputs change.
    Never mutates any previously published revision record.
    """
    now = datetime.now(timezone.utc).isoformat()
    has_outputs = bool(garment_doc.get("mesh_assets") or garment_doc.get("qa_report"))
    updates: Dict[str, Any] = {
        "updated_at": now,
    }
    if has_outputs:
        updates["downstream_stale"] = True
        updates["stale_reason"] = reason
        updates["stale_at"] = now
        if garment_doc.get("status") in ("needs_review", "approved"):
            updates["status"] = "draft"
        elif garment_doc.get("status") == "published":
            # Keep published catalog intact, mark working draft dirty for next revision
            updates["draft_dirty"] = True
            updates["status"] = "draft"
        qa = garment_doc.get("qa_report")
        if isinstance(qa, dict):
            qa_copy = dict(qa)
            qa_copy["stale"] = True
            qa_copy["stale_reason"] = reason
            updates["qa_report"] = qa_copy
    return updates


def list_revisions(garment_id: str) -> List[Dict[str, Any]]:
    ensure_garment_indexes()
    return mongo.find_documents(COLL_REVISIONS, {"garment_id": garment_id}, sort_field="revision", ascending=False)


def get_revision_doc(garment_id: str, revision: int) -> Optional[Dict[str, Any]]:
    ensure_garment_indexes()
    return mongo.find_document(COLL_REVISIONS, {"garment_id": garment_id, "revision": int(revision)})


def _next_revision_number(garment_doc: Dict[str, Any]) -> int:
    revs = list_revisions(garment_doc["id"])
    max_rev = max([int(r.get("revision", 0)) for r in revs], default=0)
    if max_rev == 0 and garment_doc.get("mesh_assets"):
        max_rev = int(garment_doc.get("revision", 1))
    return max_rev + 1


def execute_generation_pipeline(
    garment_doc: Dict[str, Any],
    brand_id: str,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Executes the pattern-first S/M/L generation pipeline with idempotency,
    private revision-scoped storage, QA hash binding, and MongoDB job/revision tracking.
    """
    ensure_garment_indexes()
    garment_id = garment_doc["id"]
    sku = garment_doc.get("sku", "TSH-WW-CREW-001")
    input_hash = compute_generation_input_hash(garment_doc)
    now = datetime.now(timezone.utc).isoformat()

    # Idempotency check: reuse existing non-failed revision for identical inputs unless forced
    if not force and not garment_doc.get("downstream_stale", False):
        existing_revs = mongo.find_documents(
            COLL_REVISIONS,
            {"garment_id": garment_id, "input_hash": input_hash},
            sort_field="revision",
            ascending=False,
            limit=1,
        )
        if existing_revs and existing_revs[0].get("status") in ("AWAITING_APPROVAL", "QA_PASSED", "APPROVED", "PUBLISHED"):
            rev_doc = existing_revs[0]
            return {
                "garment_id": garment_id,
                "revision": rev_doc["revision"],
                "job_id": rev_doc.get("job_id"),
                "idempotent_hit": True,
                "status": garment_doc.get("status", "needs_review"),
                "revision_status": rev_doc["status"],
                "confidence_level": rev_doc.get("qa_report", {}).get("confidence_level", "PARAMETRIC_TEMPLATE"),
                "pipeline_stages": rev_doc.get("pipeline_stages", []),
                "qa_report": rev_doc.get("qa_report"),
                "assets": rev_doc.get("mesh_assets"),
                "asset_checksums": rev_doc.get("asset_checksums", {}),
                "input_hash": input_hash,
                "message": f"Reused existing immutable revision rev{rev_doc['revision']} for identical inputs.",
            }

    next_rev = _next_revision_number(garment_doc)
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    started_at = datetime.now(timezone.utc).isoformat()

    job_doc = {
        "job_id": job_id,
        "garment_id": garment_id,
        "sku": sku,
        "brand_id": brand_id,
        "target_revision": next_rev,
        "input_hash": input_hash,
        "generator_version": "PatternGarmentBuilder-M2RC-v3",
        "status": "QUEUED",
        "started_at": started_at,
        "ended_at": None,
        "output_asset_ids": [],
        "qa_id": None,
        "error_details": None,
    }
    mongo.upsert_document(COLL_JOBS, {"job_id": job_id}, job_doc)
    mongo.update_document(COLL_JOBS, {"job_id": job_id}, {"status": "RUNNING"})

    available_sizes = garment_doc.get("available_sizes", ["S", "M", "L"])
    meas_dict = garment_doc.get("measurements", STANDARD_BOXY_CREW_MEASUREMENTS)
    pattern_cfg = garment_doc.get("pattern", {})
    fabric_cfg = garment_doc.get("fabric_properties", {})

    rev_dir = PRIVATE_STORAGE_ROOT / brand_id / sku / f"rev_{next_rev}"
    rev_dir.mkdir(parents=True, exist_ok=True)

    generated_meshes: Dict[str, Any] = {}
    mesh_assets: Dict[str, str] = {}
    asset_checksums: Dict[str, str] = {}
    asset_records: List[Dict[str, Any]] = []
    glb_paths_by_size: Dict[str, str] = {}

    try:
        for sz in available_sizes:
            size_meas = meas_dict.get(sz, STANDARD_BOXY_CREW_MEASUREMENTS.get(sz, STANDARD_BOXY_CREW_MEASUREMENTS["M"]))
            out_glb = str(rev_dir / f"{sku}_{sz}_rev{next_rev}.glb")
            svg_dir = str(rev_dir / "svgs" / sz)
            mesh = ParametricPatternBuilder.build_3d_geometry(
                size_meas,
                sz,
                out_glb=out_glb,
                panels_svg_dir=svg_dir,
                collar_type=pattern_cfg.get("collar_type", "ribbed_crewneck"),
                pocket_width_cm=pattern_cfg.get("pocket_width_cm"),
                pocket_height_cm=pattern_cfg.get("pocket_height_cm"),
                fabric_profile=fabric_cfg,
                sku=sku,
            )
            generated_meshes[sz] = mesh
            glb_paths_by_size[sz] = out_glb

            sha256 = GarmentAssetManager.compute_sha256(out_glb) or ""
            byte_size = os.path.getsize(out_glb)
            asset_id = f"ast-{garment_id[:8]}-r{next_rev}-{sz}"
            asset_checksums[sz] = sha256
            mesh_assets[sz] = f"/api/v1/merchant/garments/{garment_id}/revisions/{next_rev}/assets/{sz}"

            asset_doc = {
                "asset_id": asset_id,
                "owner_brand_id": brand_id,
                "garment_id": garment_id,
                "sku": sku,
                "revision": next_rev,
                "size": sz,
                "glb_file": f"{sku}_{sz}_rev{next_rev}.glb",
                "mime_type": "model/gltf-binary",
                "size_bytes": byte_size,
                "sha256": sha256,
                "storage_path": out_glb,
                "access_classification": "private",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            mongo.upsert_document(COLL_ASSETS, {"asset_id": asset_id}, asset_doc)
            asset_records.append(asset_doc)

        # Save pattern_components.json & seam_edge_map.json for canonical size M (or first available)
        ref_sz = "M" if "M" in generated_meshes else available_sizes[0]
        ref_mesh = generated_meshes[ref_sz]
        with open(rev_dir / "pattern_components.json", "w", encoding="utf-8") as f:
            json.dump(ref_mesh.get("panel_metadata", []), f, indent=2)
        with open(rev_dir / "seam_edge_map.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "seams": ref_mesh.get("seam_map", []),
                    "surface_attachments": ref_mesh.get("surface_attachments", []),
                },
                f,
                indent=2,
            )

        mesh_assets["canonical"] = mesh_assets.get("M") or mesh_assets[available_sizes[0]]
        mongo.update_document(
            COLL_JOBS,
            {"job_id": job_id},
            {"status": "GENERATED", "output_asset_ids": [a["asset_id"] for a in asset_records]},
        )

        # Run full geometry, material, measurement, and baseline mannequin fit QA
        qa_report = GarmentQAEngine.run_full_qa(
            garment_doc=garment_doc,
            generated_meshes=generated_meshes,
            fabric_profile=fabric_cfg,
            pattern_data=pattern_cfg,
            measurements=meas_dict,
            glb_paths_by_size=glb_paths_by_size,
        )
        qa_id = f"qa-{garment_id[:8]}-r{next_rev}"
        qa_report["qa_id"] = qa_id
        qa_report["garment_id"] = garment_id
        qa_report["sku"] = sku
        qa_report["revision"] = next_rev
        qa_report["input_hash"] = input_hash
        qa_report["asset_sha256_map"] = asset_checksums
        qa_report["stale"] = False
        qa_report["validation_source"] = f"WearWise Pattern-First QA Engine (rev{next_rev})"

        qa_passed = qa_report.get("overall_status") in ("PASSED", "WARNING")
        rev_status = "AWAITING_APPROVAL" if qa_passed else "FAILED"
        job_status = "AWAITING_APPROVAL" if qa_passed else "FAILED"
        garment_status = "needs_review" if qa_passed else "draft"

        mongo.upsert_document(
            COLL_QA_REPORTS,
            {"qa_id": qa_id},
            {
                "qa_id": qa_id,
                "garment_id": garment_id,
                "sku": sku,
                "brand_id": brand_id,
                "revision": next_rev,
                "overall_status": qa_report.get("overall_status"),
                "asset_sha256_map": asset_checksums,
                "report": qa_report,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        pipeline_stages = [
            {"stage": 1, "name": "Pattern boundary extraction", "status": "completed", "details": f"7 panels defined ({pattern_cfg.get('pattern_mode', 'parametric')})"},
            {"stage": 2, "name": "Seam relationship graph resolution", "status": "completed", "details": f"{len(ref_mesh.get('seam_map', []))} topological seams mapped"},
            {"stage": 3, "name": "Size variant grading", "status": "completed", "details": f"Graded sizes: {', '.join(available_sizes)}"},
            {"stage": 4, "name": "2D panel triangulation and remeshing", "status": "completed", "details": "Structured manifold panel grids"},
            {"stage": 5, "name": "3D spatial seam stitching", "status": "completed", "details": "Pattern-first 3D assembly"},
            {"stage": 6, "name": "Non-watertight cloth topology check", "status": "completed", "details": f"Euler={ref_mesh.get('euler_characteristic', -2)}"},
            {"stage": 7, "name": "Open boundary edge tagging", "status": "completed", "details": "Neckline, cuffs, hem open boundaries tagged"},
            {"stage": 8, "name": "UV unwrapping and seam preservation", "status": "completed", "details": "UV bounds [0,1] validated"},
            {"stage": 9, "name": "PBR diffuse & roughness atlas baking", "status": "completed", "details": f"Fabric {fabric_cfg.get('name', 'Waffle Knit')}"},
            {"stage": 10, "name": "Static mannequin spatial registration", "status": "completed", "details": "Static A-pose clearance verified"},
            {"stage": 11, "name": "Fabric physics metadata binding", "status": "completed", "details": f"{fabric_cfg.get('gsm', 240)} GSM bound"},
            {"stage": 12, "name": "SHA-256 asset checksum compilation", "status": "completed", "details": f"{len(asset_checksums)} GLBs hashed"},
            {"stage": 13, "name": "Digital garment package verification", "status": "completed" if qa_passed else "failed", "details": f"QA: {qa_report.get('overall_status')}"},
        ]

        size_variants_meta = {
            sz: {
                "asset_id": next(a["asset_id"] for a in asset_records if a["size"] == sz),
                "glb_file": f"{sku}_{sz}_rev{next_rev}.glb",
                "asset_url": mesh_assets[sz],
                "sha256": asset_checksums[sz],
                "size_bytes": next(a["size_bytes"] for a in asset_records if a["size"] == sz),
                "overall_prototype_qa": qa_report.get("overall_status"),
            }
            for sz in available_sizes
        }

        revision_doc = {
            "garment_id": garment_id,
            "sku": sku,
            "brand_id": brand_id,
            "revision": next_rev,
            "parent_revision": garment_doc.get("revision") if next_rev > 1 else None,
            "job_id": job_id,
            "input_hash": input_hash,
            "generator_version": "PatternGarmentBuilder-M2RC-v3",
            "status": rev_status,
            "immutable": True,
            "source_pattern": pattern_cfg,
            "source_images": garment_doc.get("images_meta", []),
            "measurements": meas_dict,
            "material_profile": fabric_cfg,
            "mesh_assets": mesh_assets,
            "size_variants": size_variants_meta,
            "asset_checksums": asset_checksums,
            "qa_id": qa_id,
            "qa_report": qa_report,
            "pipeline_stages": pipeline_stages,
            "storage_dir": str(rev_dir),
            "created_by": brand_id,
            "created_at": now,
        }
        mongo.upsert_document(COLL_REVISIONS, {"garment_id": garment_id, "revision": next_rev}, revision_doc)

        ended_at = datetime.now(timezone.utc).isoformat()
        mongo.update_document(
            COLL_JOBS,
            {"job_id": job_id},
            {"status": job_status, "qa_id": qa_id, "ended_at": ended_at},
        )

        update_garment = {
            "revision": next_rev,
            "active_revision": next_rev,
            "mesh_assets": mesh_assets,
            "size_variants": size_variants_meta,
            "asset_checksums": asset_checksums,
            "qa_report": qa_report,
            "pipeline_stages": pipeline_stages,
            "status": garment_status,
            "downstream_stale": False,
            "stale_reason": None,
            "draft_dirty": False,
            "step_completed": 6,
            "generated_at": ended_at,
            "updated_at": ended_at,
        }
        mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_garment})
        garment_doc.update(update_garment)
        record_audit_event(garment_id, sku, brand_id, f"GENERATION_{job_status}", {"revision": next_rev, "job_id": job_id, "qa_status": qa_report.get("overall_status")})

        return {
            "garment_id": garment_id,
            "revision": next_rev,
            "job_id": job_id,
            "idempotent_hit": False,
            "status": garment_status,
            "revision_status": rev_status,
            "confidence_level": qa_report.get("confidence_level"),
            "pipeline_stages": pipeline_stages,
            "qa_report": qa_report,
            "assets": mesh_assets,
            "size_variants": size_variants_meta,
            "asset_checksums": asset_checksums,
            "input_hash": input_hash,
            "message": f"Generated immutable revision rev{next_rev} ({qa_report.get('overall_status')}).",
        }

    except Exception as exc:
        mongo.update_document(
            COLL_JOBS,
            {"job_id": job_id},
            {"status": "FAILED", "error_details": str(exc), "ended_at": datetime.now(timezone.utc).isoformat()},
        )
        raise


def prepare_image_tryon_revision(
    garment_doc: Dict[str, Any],
    brand_id: str,
) -> Dict[str, Any]:
    """
    Prepares an immutable revision for sellers who selected IMAGE_ONLY try-on
    so they can verify photos & listing details and publish without forced 3D mesh generation.
    """
    ensure_garment_indexes()
    mode = str(garment_doc.get("try_on_mode") or "IMAGE_ONLY").upper()
    if mode != "IMAGE_ONLY":
        raise ValueError("Image-only preparation is only valid when try-on mode is IMAGE_ONLY. Run 3D generation instead.")
    if not has_storefront_front_photo(garment_doc):
        raise ValueError("Upload a front storefront garment photograph before verifying Image Try-On readiness.")

    garment_id = garment_doc["id"]
    sku = garment_doc.get("sku", "")
    next_rev = _next_revision_number(garment_doc)
    now = datetime.now(timezone.utc).isoformat()
    input_hash = compute_generation_input_hash(garment_doc)
    qa_id = f"qa-img-{garment_id[:8]}-r{next_rev}"
    qa_report = {
        "qa_id": qa_id,
        "garment_id": garment_id,
        "sku": sku,
        "revision": next_rev,
        "overall_status": "PASSED",
        "confidence_level": "IMAGE_VTON_READY",
        "mode": "IMAGE_ONLY",
        "summary": "Front garment photo and storefront details verified for Image Try-On.",
        "validation_source": f"WearWise Image VTON Readiness Check (rev{next_rev})",
        "asset_sha256_map": {},
        "stale": False,
    }
    revision_doc = {
        "garment_id": garment_id,
        "sku": sku,
        "brand_id": brand_id,
        "revision": next_rev,
        "parent_revision": garment_doc.get("revision") if next_rev > 1 else None,
        "job_id": None,
        "input_hash": input_hash,
        "generator_version": "ImageOnlyVerification-v1",
        "generation_mode": "IMAGE_ONLY",
        "status": "AWAITING_APPROVAL",
        "immutable": True,
        "source_images": garment_doc.get("images_meta", []),
        "measurements": garment_doc.get("measurements", {}),
        "material_profile": garment_doc.get("fabric_properties", {}),
        "mesh_assets": {},
        "size_variants": {},
        "asset_checksums": {},
        "qa_id": qa_id,
        "qa_report": qa_report,
        "pipeline_stages": [
            {"stage": 1, "name": "Storefront photo validation", "status": "completed", "details": "Front garment photo verified"},
            {"stage": 2, "name": "Image Try-On capability readiness", "status": "completed", "details": "Ready for review and publication"},
        ],
        "created_by": brand_id,
        "created_at": now,
    }
    mongo.upsert_document(COLL_REVISIONS, {"garment_id": garment_id, "revision": next_rev}, revision_doc)
    update_garment = {
        "revision": next_rev,
        "active_revision": next_rev,
        "qa_report": qa_report,
        "status": "needs_review",
        "downstream_stale": False,
        "stale_reason": None,
        "draft_dirty": False,
        "step_completed": max(garment_doc.get("step_completed", 2), 6),
        "updated_at": now,
    }
    mongo.update_document(COLL_GARMENTS, {"id": garment_id}, {"$set": update_garment})
    garment_doc.update(update_garment)
    record_audit_event(garment_id, sku, brand_id, "IMAGE_TRYON_VERIFIED", {"revision": next_rev})
    return {
        "garment_id": garment_id,
        "revision": next_rev,
        "status": "needs_review",
        "revision_status": "AWAITING_APPROVAL",
        "qa_report": qa_report,
        "message": f"Verified Image Try-On listing rev{next_rev}. Ready for approval & publishing.",
    }


def approve_revision(
    garment_doc: Dict[str, Any],
    brand_id: str,
    principal_id: str,
    approval_notes: str,
    target_revision: Optional[int] = None,
) -> Dict[str, Any]:
    ensure_garment_indexes()
    garment_id = garment_doc["id"]
    rev = int(target_revision or garment_doc.get("active_revision") or garment_doc.get("revision") or 1)
    rev_doc = get_revision_doc(garment_id, rev)
    if not rev_doc:
        raise ValueError(f"Revision rev{rev} not found for garment {garment_id}.")
    if garment_doc.get("downstream_stale"):
        raise ValueError("Inputs changed after last generation; regenerate before approving.")
    if rev_doc.get("status") not in ("AWAITING_APPROVAL", "QA_PASSED"):
        raise ValueError(f"Revision rev{rev} is in status '{rev_doc.get('status')}' and cannot be approved.")

    try_on_mode = str(garment_doc.get("try_on_mode") or "IMAGE_AND_THREE_D").upper()
    if try_on_mode in ("IMAGE_ONLY", "IMAGE_AND_THREE_D") and not has_any_storefront_photo(garment_doc):
        raise ValueError(f"Cannot approve rev{rev}: Image Try-On requires at least one storefront garment photo.")

    qa_report = rev_doc.get("qa_report") or {}
    if qa_report.get("overall_status") not in ("PASSED", "WARNING"):
        raise ValueError(f"Cannot approve rev{rev}: QA status is '{qa_report.get('overall_status', 'MISSING')}'.")

    is_image_only_rev = try_on_mode == "IMAGE_ONLY" and rev_doc.get("generation_mode") == "IMAGE_ONLY"
    if not is_image_only_rev:
        # Verify all required size 3D assets exist on disk and match recorded SHA-256 + QA report hashes
        available_sizes = garment_doc.get("available_sizes", ["S", "M", "L"])
        qa_hashes = qa_report.get("asset_sha256_map", {})
        for sz in available_sizes:
            ast = mongo.find_document(COLL_ASSETS, {"garment_id": garment_id, "revision": rev, "size": sz})
            if not ast:
                raise ValueError(f"Missing 3D size asset '{sz}' for revision rev{rev}. Run 3D model generation first.")
            sp = ast.get("storage_path", "")
            disk_sha = GarmentAssetManager.compute_sha256(sp)
            if not disk_sha:
                raise ValueError(f"3D asset file missing on disk for size '{sz}' rev{rev}.")
            if disk_sha != ast.get("sha256"):
                raise ValueError(f"Checksum mismatch on disk for size '{sz}' rev{rev}.")
            if qa_hashes and qa_hashes.get(sz) != disk_sha:
                raise ValueError(f"QA report hash mismatch for size '{sz}' rev{rev}.")

    now = datetime.now(timezone.utc).isoformat()
    approval_id = f"apr-{garment_id[:8]}-r{rev}-{uuid.uuid4().hex[:6]}"
    approval_event = {
        "approval_id": approval_id,
        "garment_id": garment_id,
        "sku": garment_doc.get("sku"),
        "brand_id": brand_id,
        "revision": rev,
        "qa_id": rev_doc.get("qa_id"),
        "asset_checksums": rev_doc.get("asset_checksums", {}),
        "approved_by": principal_id,
        "approval_notes": approval_notes,
        "approved_at": now,
    }
    mongo.upsert_document(COLL_APPROVALS, {"approval_id": approval_id}, approval_event)
    mongo.update_document(
        COLL_REVISIONS,
        {"garment_id": garment_id, "revision": rev},
        {"status": "APPROVED", "approved_by": principal_id, "approved_at": now, "approval_id": approval_id},
    )
    if rev_doc.get("job_id"):
        mongo.update_document(COLL_JOBS, {"job_id": rev_doc["job_id"]}, {"status": "APPROVED"})

    mongo.update_document(
        COLL_GARMENTS,
        {"id": garment_id},
        {
            "status": "approved",
            "approved_by": principal_id,
            "approved_at": now,
            "approval_notes": approval_notes,
            "revision": rev,
            "updated_at": now,
        },
    )
    record_audit_event(garment_id, garment_doc.get("sku", ""), brand_id, "REVISION_APPROVED", {"revision": rev, "approval_id": approval_id})
    return {
        "garment_id": garment_id,
        "status": "approved",
        "approved_by": principal_id,
        "approved_at": now,
        "revision": rev,
        "approval_id": approval_id,
        "message": f"Revision rev{rev} formally approved. Ready for catalog publication.",
    }


def _copy_approved_assets_to_published(
    garment_doc: Dict[str, Any],
    rev_doc: Dict[str, Any],
    rev: int,
) -> Dict[str, Any]:
    sku = garment_doc.get("sku", "TSH-WW-CREW-001")
    pub_dir = PUBLISHED_CATALOG_ROOT / sku / f"rev_{rev}"
    pub_dir.mkdir(parents=True, exist_ok=True)

    available_sizes = garment_doc.get("available_sizes", ["S", "M", "L"])
    glb_paths: Dict[str, str] = {}
    published_size_variants: Dict[str, Any] = {}
    qa_report = rev_doc.get("qa_report") or {}
    try_on_mode = str(garment_doc.get("try_on_mode") or "IMAGE_AND_THREE_D").upper()
    is_image_only_rev = try_on_mode == "IMAGE_ONLY" and rev_doc.get("generation_mode") == "IMAGE_ONLY"

    if not is_image_only_rev:
        for sz in available_sizes:
            ast = mongo.find_document(COLL_ASSETS, {"garment_id": garment_doc["id"], "revision": rev, "size": sz})
            if not ast or not os.path.exists(ast["storage_path"]):
                raise ValueError(f"Cannot publish rev{rev}: missing 3D asset for size {sz}.")
            dst_glb = str(pub_dir / f"{sku}_{sz}_rev{rev}.glb")
            if not os.path.exists(dst_glb):
                shutil.copy2(ast["storage_path"], dst_glb)
            sha256 = GarmentAssetManager.compute_sha256(dst_glb)
            if sha256 != ast.get("sha256"):
                raise ValueError(f"Published copy checksum mismatch for {sku} size {sz} rev{rev}.")
            glb_paths[sz] = dst_glb
            published_size_variants[sz] = {
                "glb_file": f"{sku}_{sz}_rev{rev}.glb",
                "asset_url": f"/api/products/sku/{sku}/revisions/{rev}/assets/{sz}",
                "sha256": sha256,
                "size_bytes": os.path.getsize(dst_glb),
                "overall_prototype_qa": qa_report.get("overall_status", "PASSED"),
            }

    # Copy ONLY storefront-safe images (never technical_reference-only images)
    storefront_images: List[Dict[str, Any]] = []
    for im in garment_doc.get("images_meta", []):
        roles = im.get("roles") or [im.get("role")]
        if any(r in ("storefront_gallery", "both") for r in roles):
            src_img = BODY_ENGINE_ROOT / "artifacts" / "merchant_uploads" / garment_doc["id"] / os.path.basename(str(im.get("filename_on_disk") or ""))
            if not src_img.exists() and im.get("local_path"):
                src_img = Path(im["local_path"])
            if src_img.exists():
                dst_img = pub_dir / f"storefront_{im['viewpoint']}_{im['id']}{src_img.suffix}"
                if not dst_img.exists():
                    shutil.copy2(src_img, dst_img)
                storefront_images.append({
                    "id": im["id"],
                    "viewpoint": im["viewpoint"],
                    "role": "storefront_gallery",
                    "url": f"/api/products/sku/{sku}/revisions/{rev}/images/{dst_img.name}",
                    "sha256": im.get("sha256"),
                })

    return {
        "pub_dir": str(pub_dir),
        "glb_paths": glb_paths,
        "size_variants": published_size_variants,
        "storefront_images": storefront_images,
    }


def publish_revision(
    garment_doc: Dict[str, Any],
    brand_id: str,
    publisher_id: str,
    target_revision: Optional[int] = None,
) -> Dict[str, Any]:
    with _publish_lock:
        return _publish_revision_locked(
            garment_doc=garment_doc,
            brand_id=brand_id,
            publisher_id=publisher_id,
            target_revision=target_revision,
        )


def _publish_revision_locked(
    garment_doc: Dict[str, Any],
    brand_id: str,
    publisher_id: str,
    target_revision: Optional[int] = None,
) -> Dict[str, Any]:
    ensure_garment_indexes()
    garment_id = garment_doc["id"]
    sku = garment_doc.get("sku", "TSH-WW-CREW-001")
    rev = int(target_revision or garment_doc.get("active_revision") or garment_doc.get("revision") or 1)
    rev_doc = get_revision_doc(garment_id, rev)
    if not rev_doc:
        raise ValueError(f"Revision rev{rev} not found.")
    if rev_doc.get("status") not in ("APPROVED", "PUBLISHED"):
        raise ValueError(f"Revision rev{rev} is in status '{rev_doc.get('status')}'. Explicit approval is required before publishing.")

    try_on_mode = str(garment_doc.get("try_on_mode") or "IMAGE_AND_THREE_D").upper()
    if try_on_mode in ("IMAGE_ONLY", "IMAGE_AND_THREE_D") and not has_any_storefront_photo(garment_doc):
        raise ValueError(f"Cannot publish {sku} as '{try_on_mode}' without a storefront garment photograph.")

    copied = _copy_approved_assets_to_published(garment_doc, rev_doc, rev)
    if try_on_mode in ("THREE_D_ONLY", "IMAGE_AND_THREE_D") and not copied["size_variants"]:
        raise ValueError(f"Cannot publish {sku} as '{try_on_mode}' without approved S/M/L 3D assets.")

    caps = compute_try_on_capabilities(garment_doc, size_variants=copied["size_variants"])
    now = datetime.now(timezone.utc).isoformat()
    published_ver = f"v{rev}.0"

    manifest = GarmentAssetManager.compile_package_manifest(
        garment_doc=garment_doc,
        qa_report=rev_doc.get("qa_report", {}),
        garment_dir=copied["pub_dir"],
        principal_id=publisher_id,
        revision=rev,
        glb_paths_by_size=copied["glb_paths"],
    )
    manifest["asset_urls"] = {sz: v["asset_url"] for sz, v in copied["size_variants"].items()}

    mongo.upsert_document(COLL_MANIFESTS, {"garment_id": garment_id, "revision": rev}, manifest)
    manifest_path = Path(copied["pub_dir"]) / f"{sku}_rev{rev}_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    pub_id = f"pub-{sku}-r{rev}-{uuid.uuid4().hex[:6]}"
    pub_record = {
        "publication_id": pub_id,
        "garment_id": garment_id,
        "sku": sku,
        "brand_id": brand_id,
        "revision": rev,
        "published_version": published_ver,
        "published_by": publisher_id,
        "published_at": now,
        "action": "publish",
        "size_variants": copied["size_variants"],
        "manifest": manifest,
    }
    mongo.upsert_document(COLL_PUBLICATIONS, {"publication_id": pub_id}, pub_record)

    mongo.update_document(
        COLL_REVISIONS,
        {"garment_id": garment_id, "revision": rev},
        {"status": "PUBLISHED", "published_at": now, "published_by": publisher_id, "published_dir": copied["pub_dir"]},
    )
    if rev_doc.get("job_id"):
        mongo.update_document(COLL_JOBS, {"job_id": rev_doc["job_id"]}, {"status": "PUBLISHED"})

    # Atomically update Commerce catalog pointer
    cp_col = mongo.get_commerce_collection(COLL_COMMERCE_PUBLICATIONS)
    if cp_col is not None:
        cp_col.update_one(
            {"sku": sku},
            {
                "$set": {
                    "sku": sku,
                    "garment_id": garment_id,
                    "brand_id": brand_id,
                    "name": garment_doc.get("name"),
                    "category": garment_doc.get("category", "Tops"),
                    "subcategory": garment_doc.get("subcategory", ""),
                    "description": garment_doc.get("description", ""),
                    "color_variant": garment_doc.get("color_variant", ""),
                    "price": garment_doc.get("price", 2999),
                    "currency": garment_doc.get("currency", "INR"),
                    "available_sizes": garment_doc.get("available_sizes", ["S", "M", "L"]),
                    "active_revision": rev,
                    "published_version": published_ver,
                    "status": "published",
                    "size_variants": copied["size_variants"],
                    "measurement_chart": rev_doc.get("measurements", {}),
                    "material_profile": rev_doc.get("material_profile", {}),
                    "storefront_images": copied["storefront_images"],
                    "try_on_mode": try_on_mode,
                    "try_on_capabilities": caps,
                    "seller_name": garment_doc.get("seller_name", "WearWise Studio Merchant"),
                    "qa_summary": {
                        "qa_id": rev_doc.get("qa_id"),
                        "overall_status": rev_doc.get("qa_report", {}).get("overall_status"),
                        "confidence_level": rev_doc.get("qa_report", {}).get("confidence_level"),
                        "asset_sha256_map": {sz: v["sha256"] for sz, v in copied["size_variants"].items()},
                        "validation_source": rev_doc.get("qa_report", {}).get("validation_source"),
                    },
                    "published_at": now,
                    "published_by": publisher_id,
                    "updated_at": now,
                },
                "$push": {
                    "publication_history": {
                        "publication_id": pub_id,
                        "revision": rev,
                        "published_version": published_ver,
                        "action": "publish",
                        "timestamp": now,
                        "publisher_id": publisher_id,
                    }
                },
            },
            upsert=True,
        )

    mongo.update_document(
        COLL_GARMENTS,
        {"id": garment_id},
        {
            "status": "published",
            "published_revision": rev,
            "published_version": published_ver,
            "published_at": now,
            "published_by": publisher_id,
            "try_on_mode": try_on_mode,
            "try_on_capabilities": caps,
            "manifest": manifest,
            "updated_at": now,
        },
    )
    record_audit_event(garment_id, sku, brand_id, "REVISION_PUBLISHED", {"revision": rev, "publication_id": pub_id, "try_on_mode": try_on_mode})
    return {
        "garment_id": garment_id,
        "sku": sku,
        "status": "published",
        "revision": rev,
        "published_version": published_ver,
        "published_at": now,
        "published_by": publisher_id,
        "publication_id": pub_id,
        "try_on_mode": try_on_mode,
        "try_on_capabilities": caps,
        "manifest": manifest,
        "size_variants": copied["size_variants"],
        "message": f"Published {sku} rev{rev} ({published_ver}) to active catalog.",
    }


def rollback_revision(
    garment_doc: Dict[str, Any],
    brand_id: str,
    target_revision: int,
    publisher_id: str,
    reason: str = "Catalog rollback to previously approved revision",
) -> Dict[str, Any]:
    ensure_garment_indexes()
    garment_id = garment_doc["id"]
    sku = garment_doc.get("sku", "")
    rev_doc = get_revision_doc(garment_id, target_revision)
    if not rev_doc:
        raise ValueError(f"Target revision rev{target_revision} does not exist.")
    if rev_doc.get("status") not in ("APPROVED", "PUBLISHED"):
        raise ValueError(f"Cannot rollback to rev{target_revision} (status='{rev_doc.get('status')}').")

    res = publish_revision(garment_doc, brand_id, publisher_id, target_revision=target_revision)
    record_audit_event(
        garment_id,
        sku,
        brand_id,
        "CATALOG_ROLLBACK",
        {"restored_revision": target_revision, "reason": reason, "publisher_id": publisher_id},
    )
    res["rollback"] = True
    res["reason"] = reason
    res["message"] = f"Rolled back {sku} active catalog pointer to rev{target_revision}."
    return res
