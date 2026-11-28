"""
WearWise Avatar MongoDB Repository
Handles document persistence for avatar_configurations, avatar_assets, and deletion records.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.db import mongo


class MongoAvatarRepository:
    """Document repository for 3D Avatar assets and configurations in MongoDB Atlas."""

    def __init__(self):
        self.configs_col = "avatar_configurations"
        self.assets_col = "avatar_assets"

    def create_avatar_configuration(
        self,
        revision_id: uuid.UUID,
        engine_name: str,
        engine_version: str,
        shape_spec_json: Dict[str, Any],
        adapter_metadata_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": config_id,
            "revision_id": str(revision_id),
            "engine_name": engine_name,
            "engine_version": engine_version,
            "shape_spec_json": shape_spec_json,
            "adapter_metadata_json": adapter_metadata_json,
            "created_at": now,
        }
        mongo.upsert_document(self.configs_col, {"id": config_id}, doc)
        return doc

    def create_avatar_asset(
        self,
        config_id: uuid.UUID,
        format_type: str,
        size_bytes: int,
        sha256_checksum: str,
        storage_uri: str,
        generation_duration_ms: Decimal,
        vertex_count: int,
        is_valid_manifold: bool = True,
    ) -> Dict[str, Any]:
        asset_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": asset_id,
            "config_id": str(config_id),
            "format": format_type,
            "size_bytes": size_bytes,
            "sha256_checksum": sha256_checksum,
            "storage_uri": storage_uri,
            "generation_duration_ms": float(generation_duration_ms),
            "vertex_count": vertex_count,
            "is_valid_manifold": is_valid_manifold,
            "created_at": now,
        }
        mongo.upsert_document(self.assets_col, {"id": asset_id}, doc)
        return doc

    def get_avatar_asset(self, asset_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        return mongo.find_document(self.assets_col, {"id": str(asset_id)})

    def get_avatar_assets_for_config(self, config_id: uuid.UUID) -> List[Dict[str, Any]]:
        return mongo.find_documents(self.assets_col, {"config_id": str(config_id)}, sort_field="created_at", ascending=False)
