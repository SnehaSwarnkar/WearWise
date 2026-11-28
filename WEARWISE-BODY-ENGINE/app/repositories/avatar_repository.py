"""
WearWise Avatar Repository
Manages persistence for avatar configurations, generated 3D assets, and deletion outbox records.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    AvatarConfigurationModel,
    AvatarAssetModel,
    ProfileRevisionModel,
    BodyProfileModel,
    AssetDeletionOutboxModel,
)


class AvatarRepository:
    """Repository for Avatar Configurations and 3D Assets."""

    def __init__(self, db: Session):
        self.db = db

    def create_avatar_configuration(
        self,
        revision_id: uuid.UUID,
        engine_name: str,
        engine_version: str,
        shape_spec_json: Dict[str, Any],
        adapter_metadata_json: Dict[str, Any],
    ) -> AvatarConfigurationModel:
        """Stores configuration / recipe used to produce an avatar."""
        config = AvatarConfigurationModel(
            revision_id=revision_id,
            engine_name=engine_name,
            engine_version=engine_version,
            shape_spec_json=shape_spec_json,
            adapter_metadata_json=adapter_metadata_json,
        )
        self.db.add(config)
        self.db.flush()
        return config

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
    ) -> AvatarAssetModel:
        """Stores content-addressable metadata for generated 3D avatar GLB."""
        asset = AvatarAssetModel(
            config_id=config_id,
            format=format_type,
            size_bytes=size_bytes,
            sha256_checksum=sha256_checksum,
            storage_uri=storage_uri,
            generation_duration_ms=generation_duration_ms,
            vertex_count=vertex_count,
            is_valid_manifold=is_valid_manifold,
        )
        self.db.add(asset)
        self.db.flush()
        return asset

    def get_avatar_asset(self, asset_id: uuid.UUID) -> Optional[AvatarAssetModel]:
        """Retrieves asset by id, joined with its configuration and profile revision."""
        stmt = (
            select(AvatarAssetModel)
            .where(AvatarAssetModel.id == asset_id)
            .options(
                joinedload(AvatarAssetModel.configuration)
                .joinedload(AvatarConfigurationModel.revision)
                .joinedload(ProfileRevisionModel.profile)
            )
        )
        return self.db.scalars(stmt).unique().first()

    def get_latest_avatar_asset_for_profile(self, profile_id: uuid.UUID) -> Optional[AvatarAssetModel]:
        """Retrieves the most recent avatar asset for a given profile."""
        stmt = (
            select(AvatarAssetModel)
            .join(AvatarConfigurationModel, AvatarConfigurationModel.id == AvatarAssetModel.config_id)
            .join(ProfileRevisionModel, ProfileRevisionModel.id == AvatarConfigurationModel.revision_id)
            .where(ProfileRevisionModel.profile_id == profile_id)
            .order_by(AvatarAssetModel.created_at.desc())
            .options(
                joinedload(AvatarAssetModel.configuration)
                .joinedload(AvatarConfigurationModel.revision)
                .joinedload(ProfileRevisionModel.profile)
            )
        )
        return self.db.scalars(stmt).unique().first()
