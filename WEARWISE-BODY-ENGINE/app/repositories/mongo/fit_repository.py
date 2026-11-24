"""
WearWise Fit MongoDB Repository
Handles document persistence for fit_recommendations.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.db import mongo


class MongoFitRepository:
    """Document repository for Honest Fit recommendations in MongoDB Atlas."""

    def __init__(self):
        self.recommendations_col = "fit_recommendations"

    def save_fit_recommendation(
        self,
        profile_revision_id: uuid.UUID,
        garment_revision_id: uuid.UUID,
        recommended_size: str,
        composite_score: Decimal,
        explanations_json: Dict[str, Any],
        rulebook_version: str,
    ) -> Dict[str, Any]:
        rec_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": rec_id,
            "profile_revision_id": str(profile_revision_id),
            "garment_revision_id": str(garment_revision_id),
            "recommended_size": recommended_size,
            "composite_score": float(composite_score),
            "explanations_json": explanations_json,
            "rulebook_version": rulebook_version,
            "created_at": now,
        }
        mongo.upsert_document(self.recommendations_col, {"id": rec_id}, doc)
        return doc

    def get_fit_recommendation(self, recommendation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.recommendations_col, {"id": str(recommendation_id)})

    def get_recent_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.recommendations_col, {}, sort_field="created_at", ascending=False, limit=limit)
