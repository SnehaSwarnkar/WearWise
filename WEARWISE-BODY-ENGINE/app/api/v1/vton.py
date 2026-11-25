"""
FastAPI Router for Image-Based AI Photo Virtual Try-On
Endpoint base: /api/v1/try-on/vton
Enforces explicit consent, honest provider availability, user ownership,
and private non-cached asset delivery.
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.auth import get_current_user_id
from app.services.person_image_service import ValidationError
from app.services.vton_job_service import VTONJobService
from app.services.vton_provider import (
    HonestVTONProviderAdapter,
    VTONProviderUnavailableError,
)

router = APIRouter(prefix="/try-on/vton", tags=["AI Photo Virtual Try-On"])

_provider = HonestVTONProviderAdapter()
_job_service = VTONJobService(provider=_provider)


def _require_owned_job(job_id: str, user_id: uuid.UUID) -> Dict[str, Any]:
    try:
        job = _job_service.get_job_owned(job_id, str(user_id))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Try-on job not found")
    return job


@router.get("/providers")
def get_vton_providers():
    """Returns honest AI photo try-on provider availability and hardware checks."""
    return _provider.get_provider_metadata()


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_vton_job(
    file: UploadFile = File(...),
    garment_sku: str = Form("TSH-WW-CREW-001"),
    consent: bool = Form(False),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Validates shopper consent and real-person photograph (stripping EXIF),
    then submits to an active external VTON provider or fails honestly with 503.
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
            "message": "Your photo try-on request is processing.",
            "garment_sku": garment_sku,
            "created_at": job["created_at"],
        }
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "VALIDATION_FAILED", "message": str(ve)},
        )
    except VTONProviderUnavailableError as pue:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "PROVIDER_UNAVAILABLE",
                "message": str(pue),
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "PROCESSING_FAILED", "message": str(exc)},
        )


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Retrieves current job status and progress for the owning shopper."""
    job = _require_owned_job(job_id, user_id)
    # Never expose internal filesystem path over API
    safe_job = {k: v for k, v in job.items() if k != "person_image_path"}
    return safe_job


@router.get("/jobs/{job_id}/results")
def get_job_results(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Returns completed try-on result views strictly for the owning shopper."""
    job = _require_owned_job(job_id, user_id)
    if job["status"] not in ("completed", "failed"):
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress_percent": job["progress_percent"],
            "views": {},
        }
    return _job_service.get_results(job_id)


@router.delete("/jobs/{job_id}")
def delete_vton_job(
    job_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Permanently deletes a try-on job and all generated result images for the owner."""
    _require_owned_job(job_id, user_id)
    success = _job_service.delete_job(job_id)
    return {
        "job_id": job_id,
        "deleted": success,
        "message": "Your try-on session and images have been permanently deleted.",
    }


@router.get("/images/{filename}")
def get_vton_image(
    filename: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Streams an owner-scoped generated view image with strict no-store privacy headers.
    Raw uploaded customer photographs are never exposed publicly.
    """
    if filename.startswith("person_"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Raw uploaded photos are private.")
    job_prefix = filename.split("_", 1)[0] if "_" in filename else ""
    if job_prefix:
        _require_owned_job(job_prefix, user_id)

    asset_path = _job_service.storage_service.get_asset_path(filename)
    if not asset_path or not asset_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image asset not found")
    media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
    return FileResponse(
        asset_path,
        media_type=media_type,
        headers={"Cache-Control": "private, no-store"},
    )
