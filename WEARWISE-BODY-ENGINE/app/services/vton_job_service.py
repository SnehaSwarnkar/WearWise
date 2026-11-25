"""
WearWise VTON Job Service
Orchestrates virtual try-on jobs across an honest state machine:
  queued -> preprocessing -> frontal_generation -> completed (or failed).
Enforces explicit consent, EXIF stripping, fail-closed provider readiness,
automatic temporary upload deletion, and user-owned deletion.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from app.repositories.mongo.vton_repository import MongoVTONRepository
from app.services.garment_reference_service import GarmentReferenceService
from app.services.person_image_service import PersonImageService, ValidationError
from app.services.tryon_asset_storage_service import TryOnAssetStorageService
from app.services.vton_provider import (
    BaseVTONProvider,
    HonestVTONProviderAdapter,
    VTONProviderUnavailableError,
)

logger = logging.getLogger("wearwise.vton.job_service")

_thread_pool = ThreadPoolExecutor(max_workers=4)


class VTONJobService:
    def __init__(
        self,
        person_service: Optional[PersonImageService] = None,
        garment_service: Optional[GarmentReferenceService] = None,
        storage_service: Optional[TryOnAssetStorageService] = None,
        provider: Optional[BaseVTONProvider] = None,
        repo: Optional[MongoVTONRepository] = None,
    ):
        self.person_service = person_service or PersonImageService()
        self.garment_service = garment_service or GarmentReferenceService()
        self.storage_service = storage_service or TryOnAssetStorageService()
        self.provider = provider or HonestVTONProviderAdapter()
        self.repo = repo or MongoVTONRepository()

    def create_job(
        self,
        user_id: str,
        image_bytes: bytes,
        filename: str,
        garment_sku: str,
        user_consent: bool,
    ) -> Dict[str, Any]:
        """
        Validates consent and real-person photograph (stripping EXIF), checks provider
        readiness before retaining any photo, and schedules external inference.
        """
        processed_photo = self.person_service.validate_and_process(
            image_bytes=image_bytes,
            filename=filename,
            user_consent=user_consent,
        )

        ready, unavailable_reason = self.provider.is_ready()
        if not ready:
            # Never hold onto a customer photograph when the VTON service is unavailable.
            self.person_service.delete_photo(processed_photo["file_path"])
            raise VTONProviderUnavailableError(unavailable_reason)

        job = self.repo.create_job(
            user_id=user_id,
            garment_sku=garment_sku,
            person_image_hash=processed_photo["sha256_hash"],
            person_image_path=processed_photo["file_path"],
            category="tops",
        )

        job_id = job["id"]
        _thread_pool.submit(self._execute_pipeline, job_id, processed_photo["file_path"], garment_sku)
        return job

    def _cleanup_temp_upload(self, job_id: str, person_image_path: Optional[str]) -> None:
        retain_seconds = int(os.getenv("VTON_RETAIN_TEMP_UPLOAD_SECONDS", "0"))
        if retain_seconds > 0 or not person_image_path:
            return
        deleted = self.person_service.delete_photo(person_image_path)
        if deleted:
            self.repo.update_job_fields(
                job_id,
                {"person_image_path": "", "temp_upload_deleted": True},
            )

    def _execute_pipeline(self, job_id: str, person_image_path: str, garment_sku: str):
        try:
            self.repo.update_job_status(job_id, status="preprocessing", progress_percent=20)
            garment_meta = self.garment_service.resolve_references(garment_sku)

            self.repo.update_job_status(job_id, status="frontal_generation", progress_percent=55)
            views = self.provider.generate_multiview(
                person_image_path=person_image_path,
                garment_sku=garment_sku,
                garment_metadata=garment_meta,
            )

            for view_type in ["front", "side", "back"]:
                img = views.get(view_type)
                if img is None:
                    continue
                filepath, relative_url = self.storage_service.save_view_image(job_id, view_type, img)
                view_spec = garment_meta["views"].get(view_type, {})
                self.repo.save_result(
                    job_id=job_id,
                    view_type=view_type,
                    storage_uri=filepath,
                    relative_url=relative_url,
                    is_inferred=view_spec.get("is_inferred", False),
                    confidence_score=view_spec.get("confidence", 0.95),
                )

            self.repo.update_job_status(job_id, status="completed", progress_percent=100)
        except Exception as exc:
            logger.error("Job %s failed: %s", job_id, exc, exc_info=True)
            self.repo.update_job_status(
                job_id,
                status="failed",
                progress_percent=0,
                error_message=str(exc),
            )
        finally:
            self._cleanup_temp_upload(job_id, person_image_path)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_job(job_id)

    def get_job_owned(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        job = self.repo.get_job(job_id)
        if not job:
            return None
        if str(job.get("user_id")) != str(user_id):
            raise PermissionError("Access denied: try-on job belongs to another account.")
        return job

    def get_results(self, job_id: str) -> Dict[str, Any]:
        job = self.repo.get_job(job_id)
        if not job:
            return {"error": "Job not found"}

        results = self.repo.get_results_by_job(job_id)
        garment_meta = self.garment_service.resolve_references(job["garment_sku"])
        provider_meta = self.provider.get_provider_metadata()

        views_dict: Dict[str, Any] = {}
        for r in results:
            v_type = r["view_type"]
            v_meta = garment_meta["views"].get(v_type, {})
            views_dict[v_type] = {
                "id": r["id"],
                "view_type": v_type,
                "url": r["relative_url"],
                "is_inferred": r["is_inferred"],
                "confidence_score": r["confidence_score"],
                "disclaimer": v_meta.get("disclaimer"),
                "description": v_meta.get("description"),
            }

        return {
            "job_id": job_id,
            "status": job["status"],
            "progress_percent": job["progress_percent"],
            "error_message": job.get("error_message"),
            "garment_sku": job["garment_sku"],
            "garment_title": garment_meta["title"],
            "created_at": job["created_at"],
            "temp_upload_deleted": bool(job.get("temp_upload_deleted", False)),
            "views": views_dict,
            "provenance": {
                "provider_name": provider_meta.get("provider_name"),
                "storage_policy": "Private shopper-scoped storage with immediate input photo deletion after inference.",
            },
        }

    def delete_job(self, job_id: str) -> bool:
        job = self.repo.get_job(job_id)
        person_image_path = job.get("person_image_path") if job else None
        self.storage_service.delete_job_assets(job_id, person_image_path)
        return self.repo.delete_job_and_results(job_id)
