"""
FastAPI Router for Mode B AI Photo Virtual Try-On
Endpoint base: /api/v1/try-on/vton
"""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Response
from fastapi.responses import FileResponse

from app.api.auth import get_current_user_id
from app.services.vton_job_service import VTONJobService
from app.services.person_image_service import ValidationError
from app.services.vton_provider import DeterministicMultiViewProvider

router = APIRouter(prefix="/try-on/vton", tags=["AI Photo Virtual Try-On"])

# Service singleton
_job_service = VTONJobService()
_provider = DeterministicMultiViewProvider()


@router.get("/providers")
def get_vton_providers():
    """
    Returns hardware verification telemetry, local VRAM status, and candidate model assessments
    (FASHN VTON v1.5 and WACV 2026 multi-view research).
    """
    return _provider.get_provider_metadata()


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_vton_job(
    file: UploadFile = File(...),
    garment_sku: str = Form("TSH-WW-CREW-001"),
    consent: bool = Form(True),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Initiates an asynchronous multi-view virtual try-on job for an uploaded real-person photograph.
    Accepts real-person photographs only. Rejects synthetic Anny avatars.
    """
    try:
        content = await file.read()
        job = _job_service.create_job(
            user_id=str(user_id),
            image_bytes=content,
            filename=file.filename or "person.jpg",
            garment_sku=garment_sku,
            user_consent=consent,
        )
        return {
            "job_id": job["id"],
            "status": job["status"],
            "message": "AI Photo Virtual Try-On job queued successfully. Generating 3 distinct views (Front, Side, Back).",
            "garment_sku": garment_sku,
            "created_at": job["created_at"],
        }
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "VALIDATION_FAILED", "message": str(ve)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "PROCESSING_FAILED", "message": str(e)},
        )


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Retrieves current job status, lifecycle stage, and progress percentage."""
    job = _job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VTON job not found")
    return job


@router.get("/jobs/{job_id}/results")
def get_job_results(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Returns the three distinct generated view images (Front, Side, Back)
    along with confidence scores and inferred view disclaimers.
    """
    job = _job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VTON job not found")

    if job["status"] not in ("completed", "failed"):
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress_percent": job.get("progress_percent", 0),
            "message": f"Job is currently {job['status']}. Please poll until completed.",
        }

    return _job_service.get_results(job_id)


@router.delete("/jobs/{job_id}")
def delete_vton_job(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Permanently deletes try-on job, uploaded photograph, and all 3 generated view assets.
    """
    job = _job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VTON job not found")

    success = _job_service.delete_job(job_id)
    return {
        "job_id": job_id,
        "deleted": success,
        "message": "Job records and all associated image assets permanently removed.",
    }


@router.get("/images/{filename}")
def get_vton_image(filename: str):
    """
    Streams an individually addressable generated view asset or uploaded photograph.
    """
    asset_path = _job_service.storage_service.get_asset_path(filename)
    if not asset_path or not asset_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image asset not found")
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(asset_path, media_type=media_type)
