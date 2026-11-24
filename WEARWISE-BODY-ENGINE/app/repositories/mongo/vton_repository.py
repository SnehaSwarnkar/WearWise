"""
WearWise VTON MongoDB Repository
Handles document persistence for virtual try-on jobs and generated view results.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.db import mongo


class MongoVTONRepository:
    """Document repository for AI Photo Virtual Try-On jobs and multi-view results."""

    def __init__(self):
        self.jobs_col = "vton_jobs"
        self.results_col = "vton_results"

    def create_job(
        self,
        user_id: str,
        garment_sku: str,
        person_image_hash: str,
        person_image_path: str,
        category: str = "tops",
    ) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        job_doc = {
            "id": job_id,
            "user_id": user_id,
            "garment_sku": garment_sku,
            "person_image_hash": person_image_hash,
            "person_image_path": person_image_path,
            "category": category,
            "status": "queued",  # queued, preprocessing, frontal_generation, multiview_generation, completed, failed
            "progress_percent": 0,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        mongo.upsert_document(self.jobs_col, {"id": job_id}, job_doc)
        return job_doc

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress_percent: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        updates = {
            "status": status,
            "progress_percent": progress_percent,
            "updated_at": now,
        }
        if error_message is not None:
            updates["error_message"] = error_message
        mongo.upsert_document(self.jobs_col, {"id": job_id}, updates)
        return mongo.find_document(self.jobs_col, {"id": job_id})

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.jobs_col, {"id": job_id})

    def save_result(
        self,
        job_id: str,
        view_type: str,  # "front", "side", "back"
        storage_uri: str,
        relative_url: str,
        is_inferred: bool = False,
        confidence_score: float = 0.95,
    ) -> Dict[str, Any]:
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        result_doc = {
            "id": result_id,
            "job_id": job_id,
            "view_type": view_type,
            "storage_uri": storage_uri,
            "relative_url": relative_url,
            "is_inferred": is_inferred,
            "confidence_score": confidence_score,
            "created_at": now,
        }
        mongo.upsert_document(self.results_col, {"id": result_id}, result_doc)
        return result_doc

    def get_results_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.results_col, {"job_id": job_id}, sort_field="created_at", ascending=True)

    def delete_job_and_results(self, job_id: str) -> bool:
        mongo.delete_document(self.jobs_col, {"id": job_id})
        # Delete related results
        db = mongo.get_db()
        if db is not None:
            db[self.results_col].delete_many({"job_id": job_id})
        return True
