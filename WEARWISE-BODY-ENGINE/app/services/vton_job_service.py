"""
WearWise VTON Job Service
Orchestrates asynchronous virtual try-on jobs across the state machine:
  queued -> preprocessing -> frontal_generation -> multiview_generation -> completed (or failed).
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

from app.services.person_image_service import PersonImageService, ValidationError
from app.services.garment_reference_service import GarmentReferenceService
from app.services.tryon_asset_storage_service import TryOnAssetStorageService
from app.services.vton_provider import DeterministicMultiViewProvider, BaseVTONProvider
from app.repositories.mongo.vton_repository import MongoVTONRepository

logger = logging.getLogger("wearwise.vton.job_service")

# Background thread pool for synthetic image processing without blocking asyncio event loop
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
        self.provider = provider or DeterministicMultiViewProvider()
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
        Validates photograph, initializes asynchronous try-on job in MongoDB, and triggers processing.
        """
        # 1. Validate real-person photograph and obtain hash
        processed_photo = self.person_service.validate_and_process(
            image_bytes=image_bytes,
            filename=filename,
            user_consent=user_consent,
        )

        # 2. Create job in MongoDB repository
        job = self.repo.create_job(
            user_id=user_id,
            garment_sku=garment_sku,
            person_image_hash=processed_photo["sha256_hash"],
            person_image_path=processed_photo["file_path"],
            category="tops",
        )

        job_id = job["id"]

        # 3. Schedule asynchronous generation
        _thread_pool.submit(self._execute_pipeline, job_id, processed_photo["file_path"], garment_sku)

        return job

    def _execute_pipeline(self, job_id: str, person_image_path: str, garment_sku: str):
        """
        Executes pipeline through finite states:
          queued -> preprocessing -> frontal_generation -> multiview_generation -> completed.
        """
        try:
            # Stage 1: Preprocessing
            logger.info(f"Job {job_id}: Preprocessing input photograph...")
            self.repo.update_job_status(job_id, status="preprocessing", progress_percent=20)

            # Resolve garment reference imagery & metadata
            garment_meta = self.garment_service.resolve_references(garment_sku)

            # Stage 2: Frontal Try-On Generation
            logger.info(f"Job {job_id}: Generating frontal virtual try-on...")
            self.repo.update_job_status(job_id, status="frontal_generation", progress_percent=50)

            # Stage 3: Multi-View Synthesis (Front, Side, Back)
            logger.info(f"Job {job_id}: Generating multi-view perspectives (Front, Side, Back)...")
            self.repo.update_job_status(job_id, status="multiview_generation", progress_percent=75)

            views = self.provider.generate_multiview(
                person_image_path=person_image_path,
                garment_sku=garment_sku,
                garment_metadata=garment_meta,
            )

            # Save each of the three images as a separate, individually addressable asset
            for view_type in ["front", "side", "back"]:
                img = views[view_type]
                filepath, relative_url = self.storage_service.save_view_image(job_id, view_type, img)

                view_spec = garment_meta["views"].get(view_type, {})
                is_inferred = view_spec.get("is_inferred", False)
                confidence = view_spec.get("confidence", 0.95)

                self.repo.save_result(
                    job_id=job_id,
                    view_type=view_type,
                    storage_uri=filepath,
                    relative_url=relative_url,
                    is_inferred=is_inferred,
                    confidence_score=confidence,
                )

            # Stage 4: Completed
            logger.info(f"Job {job_id}: Successfully completed multi-view virtual try-on.")
            self.repo.update_job_status(job_id, status="completed", progress_percent=100)

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            self.repo.update_job_status(
                job_id,
                status="failed",
                progress_percent=0,
                error_message=str(e),
            )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_job(job_id)

    def get_results(self, job_id: str) -> Dict[str, Any]:
        job = self.repo.get_job(job_id)
        if not job:
            return {"error": "Job not found"}

        results = self.repo.get_results_by_job(job_id)
        garment_meta = self.garment_service.resolve_references(job["garment_sku"])

        # Map to canonical 3-view schema
        views_dict = {}
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
            "garment_sku": job["garment_sku"],
            "garment_title": garment_meta["title"],
            "created_at": job["created_at"],
            "views": views_dict,
            "provenance": {
                "multiview_method": "DeterministicMultiViewSynthesisEngine",
                "inferred_views_note": "Back and side views are AI-inferred from frontal design; back graphics and rear closures provisional.",
                "storage_policy": "Session-scoped private storage; user may delete assets at any time.",
            },
        }

    def delete_job(self, job_id: str) -> bool:
        job = self.repo.get_job(job_id)
        person_image_path = job.get("person_image_path") if job else None

        # Clean disk assets
        self.storage_service.delete_job_assets(job_id, person_image_path)
        # Delete MongoDB records
        return self.repo.delete_job_and_results(job_id)
