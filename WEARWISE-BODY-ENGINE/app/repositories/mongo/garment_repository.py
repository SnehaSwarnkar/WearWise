"""
WearWise Garment MongoDB Repository
Handles document persistence for garment_profiles, garment_revisions, garment_sizes, and garment_measurements.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.db import mongo


class MongoGarmentRepository:
    """Document repository for Garment profiles and specifications in MongoDB Atlas."""

    def __init__(self):
        self.garments_col = "garment_profiles"
        self.revisions_col = "garment_revisions"
        self.sizes_col = "garment_sizes"
        self.measurements_col = "garment_measurements"

    def create_garment(
        self,
        brand_id: uuid.UUID,
        sku: str,
        title: str,
        category: str,
        fabric_properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        garment_id = str(uuid.uuid4())
        rev_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        garment_doc = {
            "id": garment_id,
            "brand_id": str(brand_id),
            "sku": sku,
            "title": title,
            "category": category,
            "current_revision": 1,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
        mongo.upsert_document(self.garments_col, {"id": garment_id}, garment_doc)

        rev_doc = {
            "id": rev_id,
            "garment_id": garment_id,
            "revision_number": 1,
            "fabric_properties_json": fabric_properties,
            "created_at": now,
        }
        mongo.upsert_document(self.revisions_col, {"id": rev_id}, rev_doc)

        return garment_doc

    def get_garment(self, garment_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.garments_col, {"id": str(garment_id), "is_deleted": False})

    def get_garment_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.garments_col, {"sku": sku, "is_deleted": False})

    def list_garments(self, brand_id: uuid.UUID) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.garments_col, {"brand_id": str(brand_id), "is_deleted": False})

    def get_latest_revision(self, garment_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        revs = mongo.find_documents(self.revisions_col, {"garment_id": str(garment_id)}, sort_field="revision_number", ascending=False, limit=1)
        if revs:
            return revs[0]
        return None

    def get_sizes_for_revision(self, revision_id: uuid.UUID) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.sizes_col, {"revision_id": str(revision_id)})
