"""
WearWise Profile MongoDB Repository
Handles document persistence for body_profiles, profile_revisions, body_measurements, and body_shape_controls.
"""

import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.db import mongo


class MongoProfileRepository:
    """Document repository for BodyProfile and revision aggregates in MongoDB Atlas."""

    def __init__(self):
        self.profiles_col = "body_profiles"
        self.revisions_col = "profile_revisions"
        self.measurements_col = "body_measurements"
        self.controls_col = "body_shape_controls"

    def create_profile(
        self,
        user_id: uuid.UUID,
        presentation_gender: str,
        stature_cm: Decimal,
        reported_weight_kg: Optional[Decimal] = None,
        initial_controls: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        profile_id = str(uuid.uuid4())
        rev_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        profile_doc = {
            "id": profile_id,
            "user_id": str(user_id),
            "current_revision": 1,
            "presentation_gender": presentation_gender,
            "stature_cm": float(stature_cm),
            "reported_weight_kg": float(reported_weight_kg) if reported_weight_kg is not None else None,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
        }
        mongo.upsert_document(self.profiles_col, {"id": profile_id}, profile_doc)

        rev_doc = {
            "id": rev_id,
            "profile_id": profile_id,
            "revision_number": 1,
            "created_at": now,
        }
        mongo.upsert_document(self.revisions_col, {"id": rev_id}, rev_doc)

        meas_id = str(uuid.uuid4())
        meas_doc = {
            "id": meas_id,
            "revision_id": rev_id,
            "measurement_code": "stature",
            "value_cm": float(stature_cm),
            "unit": "cm",
            "acquisition_method": "user_reported",
            "validation_state": "unvalidated",
            "lifecycle_status": "active",
            "assessment_state": "eligible",
            "landmark_convention": "plantar_to_vertex_bounding_box",
            "tolerance_cm": 1.0,
            "reliability_weight": 1.0,
            "created_at": now,
        }
        mongo.upsert_document(self.measurements_col, {"id": meas_id}, meas_doc)

        ctrls = initial_controls or {}
        ctrl_id = str(uuid.uuid4())
        ctrl_doc = {
            "id": ctrl_id,
            "revision_id": rev_id,
            "shoulder_width": float(ctrls.get("shoulder_width", 0.50)),
            "chest_fullness": float(ctrls.get("chest_fullness", 0.50)),
            "belly_fullness": float(ctrls.get("belly_fullness", 0.50)),
            "waist_definition": float(ctrls.get("waist_definition", 0.50)),
            "arm_fullness": float(ctrls.get("arm_fullness", 0.50)),
            "hip_fullness": float(ctrls.get("hip_fullness", 0.50)),
            "thigh_fullness": float(ctrls.get("thigh_fullness", 0.50)),
            "calf_fullness": float(ctrls.get("calf_fullness", 0.50)),
            "created_at": now,
        }
        mongo.upsert_document(self.controls_col, {"id": ctrl_id}, ctrl_doc)

        return profile_doc

    def get_profile(self, profile_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.profiles_col, {"id": str(profile_id), "is_deleted": False})

    def list_profiles(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.profiles_col, {"user_id": str(user_id), "is_deleted": False}, sort_field="created_at", ascending=False)

    def get_latest_revision(self, profile_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        revisions = mongo.find_documents(self.revisions_col, {"profile_id": str(profile_id)}, sort_field="revision_number", ascending=False, limit=1)
        if revisions:
            return revisions[0]
        return None

    def get_measurements_for_revision(self, revision_id: uuid.UUID) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.measurements_col, {"revision_id": str(revision_id)})

    def get_controls_for_revision(self, revision_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.controls_col, {"revision_id": str(revision_id)})
