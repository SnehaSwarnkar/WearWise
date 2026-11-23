"""
WearWise SQLAlchemy 2.0 ORM Models
Corresponds 1:1 with the 12 authoritative database tables defined in DATABASE_SCHEMA.md Rev 1.2.1.
Compatible with SQLite 3 (WAL mode) and PostgreSQL 16+.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BodyProfileModel(Base):
    """
    1. body_profiles: Persistent shopper identity anchor.
    """
    __tablename__ = "body_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    presentation_gender: Mapped[str] = mapped_column(String(16), nullable=False)
    stature_cm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reported_weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    revisions: Mapped[List["ProfileRevisionModel"]] = relationship(
        "ProfileRevisionModel", back_populates="profile", cascade="all, delete-orphan", order_by="ProfileRevisionModel.revision_number"
    )


class ProfileRevisionModel(Base):
    """
    2. profile_revisions: Immutable revision history.
    """
    __tablename__ = "profile_revisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("body_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    profile: Mapped["BodyProfileModel"] = relationship("BodyProfileModel", back_populates="revisions")
    measurements: Mapped[List["BodyMeasurementModel"]] = relationship(
        "BodyMeasurementModel", back_populates="revision", cascade="all, delete-orphan"
    )
    shape_controls: Mapped[Optional["BodyShapeControlsModel"]] = relationship(
        "BodyShapeControlsModel", back_populates="revision", uselist=False, cascade="all, delete-orphan"
    )
    avatar_configurations: Mapped[List["AvatarConfigurationModel"]] = relationship(
        "AvatarConfigurationModel", back_populates="revision", cascade="all, delete-orphan"
    )
    fit_recommendations: Mapped[List["FitRecommendationModel"]] = relationship(
        "FitRecommendationModel", back_populates="profile_revision", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("profile_id", "revision_number", name="uq_profile_revision"),
    )


class BodyMeasurementModel(Base):
    """
    3. body_measurements: Canonical physical body dimensions in cm.
    """
    __tablename__ = "body_measurements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    measurement_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value_cm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(8), nullable=False, default="cm")
    acquisition_method: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_state: Mapped[str] = mapped_column(String(32), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(16), nullable=False)
    assessment_state: Mapped[str] = mapped_column(String(16), nullable=False)
    landmark_convention: Mapped[str] = mapped_column(String(128), nullable=False)
    tolerance_cm: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    reliability_weight: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("1.00"))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    revision: Mapped["ProfileRevisionModel"] = relationship("ProfileRevisionModel", back_populates="measurements")

    __table_args__ = (
        UniqueConstraint("revision_id", "measurement_code", name="uq_rev_measurement_code"),
    )


class BodyShapeControlsModel(Base):
    """
    4. body_shape_controls: Semantic slider controls for a profile revision.
    """
    __tablename__ = "body_shape_controls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    shoulder_width: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    chest_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    belly_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    waist_definition: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    arm_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    hip_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    thigh_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))
    calf_fullness: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=Decimal("0.50"))

    revision: Mapped["ProfileRevisionModel"] = relationship("ProfileRevisionModel", back_populates="shape_controls")


class AvatarConfigurationModel(Base):
    """
    5. avatar_configurations: Engine-specific generation recipe and metadata.
    """
    __tablename__ = "avatar_configurations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_name: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    shape_spec_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    adapter_metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    revision: Mapped["ProfileRevisionModel"] = relationship("ProfileRevisionModel", back_populates="avatar_configurations")
    assets: Mapped[List["AvatarAssetModel"]] = relationship(
        "AvatarAssetModel", back_populates="configuration", cascade="all, delete-orphan"
    )


class AvatarAssetModel(Base):
    """
    6. avatar_assets: Content-addressable binary mesh asset metadata.
    """
    __tablename__ = "avatar_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("avatar_configurations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    format: Mapped[str] = mapped_column(String(8), nullable=False, default="glb")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    generation_duration_ms: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    vertex_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_valid_manifold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    configuration: Mapped["AvatarConfigurationModel"] = relationship("AvatarConfigurationModel", back_populates="assets")


class GarmentProfileModel(Base):
    """
    7. garment_profiles: Garment catalog master owned by merchant brand.
    """
    __tablename__ = "garment_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    revisions: Mapped[List["GarmentRevisionModel"]] = relationship(
        "GarmentRevisionModel", back_populates="garment", cascade="all, delete-orphan", order_by="GarmentRevisionModel.revision_number"
    )

    __table_args__ = (
        UniqueConstraint("brand_id", "sku", name="uq_brand_sku"),
    )


class GarmentRevisionModel(Base):
    """
    8. garment_revisions: Garment specification revisions with fabric properties.
    """
    __tablename__ = "garment_revisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("garment_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    fabric_properties_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    garment: Mapped["GarmentProfileModel"] = relationship("GarmentProfileModel", back_populates="revisions")
    sizes: Mapped[List["GarmentSizeModel"]] = relationship(
        "GarmentSizeModel", back_populates="revision", cascade="all, delete-orphan", order_by="GarmentSizeModel.sort_order"
    )
    fit_recommendations: Mapped[List["FitRecommendationModel"]] = relationship(
        "FitRecommendationModel", back_populates="garment_revision", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("garment_id", "revision_number", name="uq_garment_revision"),
    )


class GarmentSizeModel(Base):
    """
    9. garment_sizes: Sizing labels and variants (e.g. S, M, L, XL).
    """
    __tablename__ = "garment_sizes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garment_revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("garment_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    size_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    revision: Mapped["GarmentRevisionModel"] = relationship("GarmentRevisionModel", back_populates="sizes")
    measurements: Mapped[List["GarmentMeasurementModel"]] = relationship(
        "GarmentMeasurementModel", back_populates="size", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("garment_revision_id", "size_label", name="uq_garment_size_label"),
    )


class GarmentMeasurementModel(Base):
    """
    10. garment_measurements: Finished garment dimensions and provenance.
    """
    __tablename__ = "garment_measurements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    size_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("garment_sizes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension_code: Mapped[str] = mapped_column(String(64), nullable=False)
    value_cm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    tolerance_cm: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    measurement_procedure: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance: Mapped[str] = mapped_column(String(32), nullable=False, default="brand_size_chart")

    size: Mapped["GarmentSizeModel"] = relationship("GarmentSizeModel", back_populates="measurements")

    __table_args__ = (
        UniqueConstraint("size_id", "dimension_code", name="uq_size_dimension"),
    )


class FitRecommendationModel(Base):
    """
    11. fit_recommendations: Persisted Honest Fit recommendation evaluations.
    """
    __tablename__ = "fit_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    garment_revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("garment_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommended_size: Mapped[str] = mapped_column(String(32), nullable=False)
    composite_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    explanations_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    rulebook_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    profile_revision: Mapped["ProfileRevisionModel"] = relationship("ProfileRevisionModel", back_populates="fit_recommendations")
    garment_revision: Mapped["GarmentRevisionModel"] = relationship("GarmentRevisionModel", back_populates="fit_recommendations")


class AssetDeletionOutboxModel(Base):
    """
    12. asset_deletion_outbox: Unconstrained references to deleted assets for asynchronous blob cleanup.
    """
    __tablename__ = "asset_deletion_outbox"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
