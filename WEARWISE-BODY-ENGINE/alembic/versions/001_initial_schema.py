"""001_initial_schema: Initial migration for all 12 authoritative database tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-24 10:00:00.000000

Authoritative WearWise Schema Rev 1.2.1:
  1. body_profiles
  2. profile_revisions
  3. body_measurements
  4. body_shape_controls
  5. avatar_configurations
  6. avatar_assets
  7. garment_profiles
  8. garment_revisions
  9. garment_sizes
  10. garment_measurements
  11. fit_recommendations
  12. asset_deletion_outbox

Supports both:
  - Clean initialization from an empty database.
  - Safe, idempotent upgrade of an already initialized database.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. body_profiles
    if "body_profiles" not in existing_tables:
        op.create_table(
            "body_profiles",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("current_revision", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("presentation_gender", sa.String(length=16), nullable=False),
            sa.Column("stature_cm", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("reported_weight_kg", sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        )
        op.create_index("idx_body_profiles_user_id", "body_profiles", ["user_id"])

    # 2. profile_revisions
    if "profile_revisions" not in existing_tables:
        op.create_table(
            "profile_revisions",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("profile_id", sa.Uuid(as_uuid=True), sa.ForeignKey("body_profiles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("revision_number", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
            sa.UniqueConstraint("profile_id", "revision_number", name="uq_profile_revision"),
        )
        op.create_index("idx_profile_revisions_profile_id", "profile_revisions", ["profile_id"])

    # 3. body_measurements
    if "body_measurements" not in existing_tables:
        op.create_table(
            "body_measurements",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("measurement_code", sa.String(length=64), nullable=False),
            sa.Column("value_cm", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("unit", sa.String(length=8), nullable=False, server_default="cm"),
            sa.Column("acquisition_method", sa.String(length=32), nullable=False),
            sa.Column("validation_state", sa.String(length=32), nullable=False),
            sa.Column("lifecycle_status", sa.String(length=16), nullable=False),
            sa.Column("assessment_state", sa.String(length=16), nullable=False),
            sa.Column("landmark_convention", sa.String(length=128), nullable=False),
            sa.Column("tolerance_cm", sa.Numeric(precision=4, scale=2), nullable=False, server_default="1.00"),
            sa.Column("reliability_weight", sa.Numeric(precision=3, scale=2), nullable=False, server_default="1.00"),
            sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
            sa.UniqueConstraint("revision_id", "measurement_code", name="uq_rev_measurement_code"),
        )
        op.create_index("idx_body_measurements_revision_id", "body_measurements", ["revision_id"])
        op.create_index("idx_body_measurements_code", "body_measurements", ["measurement_code"])

    # 4. body_shape_controls
    if "body_shape_controls" not in existing_tables:
        op.create_table(
            "body_shape_controls",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("shoulder_width", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("chest_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("belly_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("waist_definition", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("arm_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("hip_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("thigh_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
            sa.Column("calf_fullness", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.50"),
        )

    # 5. avatar_configurations
    if "avatar_configurations" not in existing_tables:
        op.create_table(
            "avatar_configurations",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("engine_name", sa.String(length=64), nullable=False),
            sa.Column("engine_version", sa.String(length=32), nullable=False),
            sa.Column("shape_spec_json", sa.JSON(), nullable=False),
            sa.Column("adapter_metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        )
        op.create_index("idx_avatar_configurations_revision_id", "avatar_configurations", ["revision_id"])

    # 6. avatar_assets
    if "avatar_assets" not in existing_tables:
        op.create_table(
            "avatar_assets",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("config_id", sa.Uuid(as_uuid=True), sa.ForeignKey("avatar_configurations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("format", sa.String(length=8), nullable=False, server_default="glb"),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
            sa.Column("storage_uri", sa.String(length=512), nullable=False),
            sa.Column("generation_duration_ms", sa.Numeric(precision=7, scale=2), nullable=False),
            sa.Column("vertex_count", sa.Integer(), nullable=False),
            sa.Column("is_valid_manifold", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        )
        op.create_index("idx_avatar_assets_config_id", "avatar_assets", ["config_id"])
        op.create_index("idx_avatar_assets_sha256", "avatar_assets", ["sha256_checksum"])

    # 7. garment_profiles
    if "garment_profiles" not in existing_tables:
        op.create_table(
            "garment_profiles",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("brand_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("sku", sa.String(length=64), nullable=False),
            sa.Column("title", sa.String(length=256), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("current_revision", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
            sa.UniqueConstraint("brand_id", "sku", name="uq_brand_sku"),
        )
        op.create_index("idx_garment_profiles_brand_id", "garment_profiles", ["brand_id"])

    # 8. garment_revisions
    if "garment_revisions" not in existing_tables:
        op.create_table(
            "garment_revisions",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("garment_id", sa.Uuid(as_uuid=True), sa.ForeignKey("garment_profiles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("revision_number", sa.Integer(), nullable=False),
            sa.Column("fabric_properties_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
            sa.UniqueConstraint("garment_id", "revision_number", name="uq_garment_revision"),
        )
        op.create_index("idx_garment_revisions_garment_id", "garment_revisions", ["garment_id"])

    # 9. garment_sizes
    if "garment_sizes" not in existing_tables:
        op.create_table(
            "garment_sizes",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("garment_revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("garment_revisions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("size_label", sa.String(length=32), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("garment_revision_id", "size_label", name="uq_garment_size_label"),
        )
        op.create_index("idx_garment_sizes_revision_id", "garment_sizes", ["garment_revision_id"])

    # 10. garment_measurements
    if "garment_measurements" not in existing_tables:
        op.create_table(
            "garment_measurements",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("size_id", sa.Uuid(as_uuid=True), sa.ForeignKey("garment_sizes.id", ondelete="CASCADE"), nullable=False),
            sa.Column("dimension_code", sa.String(length=64), nullable=False),
            sa.Column("value_cm", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("tolerance_cm", sa.Numeric(precision=4, scale=2), nullable=False, server_default="1.00"),
            sa.Column("measurement_procedure", sa.String(length=64), nullable=False),
            sa.Column("provenance", sa.String(length=32), nullable=False, server_default="brand_size_chart"),
            sa.UniqueConstraint("size_id", "dimension_code", name="uq_size_dimension"),
        )
        op.create_index("idx_garment_measurements_size_id", "garment_measurements", ["size_id"])

    # 11. fit_recommendations
    if "fit_recommendations" not in existing_tables:
        op.create_table(
            "fit_recommendations",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("profile_revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("profile_revisions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("garment_revision_id", sa.Uuid(as_uuid=True), sa.ForeignKey("garment_revisions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("recommended_size", sa.String(length=32), nullable=False),
            sa.Column("composite_score", sa.Numeric(precision=5, scale=2), nullable=False),
            sa.Column("explanations_json", sa.JSON(), nullable=False),
            sa.Column("rulebook_version", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        )
        op.create_index("idx_fit_recommendations_profile_rev_id", "fit_recommendations", ["profile_revision_id"])
        op.create_index("idx_fit_recommendations_garment_rev_id", "fit_recommendations", ["garment_revision_id"])

    # 12. asset_deletion_outbox
    if "asset_deletion_outbox" not in existing_tables:
        op.create_table(
            "asset_deletion_outbox",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
            sa.Column("asset_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("sha256_checksum", sa.String(length=64), nullable=False),
            sa.Column("storage_uri", sa.String(length=512), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()),
        )
        op.create_index("idx_asset_deletion_outbox_status", "asset_deletion_outbox", ["status"])


def downgrade() -> None:
    op.drop_table("asset_deletion_outbox")
    op.drop_table("fit_recommendations")
    op.drop_table("garment_measurements")
    op.drop_table("garment_sizes")
    op.drop_table("garment_revisions")
    op.drop_table("garment_profiles")
    op.drop_table("avatar_assets")
    op.drop_table("avatar_configurations")
    op.drop_table("body_shape_controls")
    op.drop_table("body_measurements")
    op.drop_table("profile_revisions")
    op.drop_table("body_profiles")
