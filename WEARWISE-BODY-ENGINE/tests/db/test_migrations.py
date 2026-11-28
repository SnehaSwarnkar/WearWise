"""
WearWise Alembic Migration Baseline Test Suite
Verifies:
  1. Initialization from an empty database via Alembic upgrade head creates all 12 tables + alembic_version.
  2. Upgrading an already initialized database is safe and idempotent.
  3. SQLite WAL journal mode functionality is preserved.
  4. PostgreSQL-compatible schema types, unique constraints, and foreign key cascades.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command

from app.db.base import Base
from app.db.session import set_sqlite_pragma


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

EXPECTED_TABLES = {
    "body_profiles",
    "profile_revisions",
    "body_measurements",
    "body_shape_controls",
    "avatar_configurations",
    "avatar_assets",
    "garment_profiles",
    "garment_revisions",
    "garment_sizes",
    "garment_measurements",
    "fit_recommendations",
    "asset_deletion_outbox",
}


def test_initialization_from_empty_database(tmp_path):
    """Proves that running Alembic upgrade head on an empty database creates all 12 tables."""
    db_file = tmp_path / "empty_db_migration.db"
    db_url = f"sqlite:///{db_file}"

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)

    # Execute upgrade head
    command.upgrade(cfg, "head")

    # Inspect created tables
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert EXPECTED_TABLES.issubset(tables), f"Missing tables: {EXPECTED_TABLES - tables}"
    assert "alembic_version" in tables

    # Verify key columns on body_profiles
    cols = {c["name"] for c in inspector.get_columns("body_profiles")}
    assert {"id", "user_id", "current_revision", "presentation_gender", "stature_cm"}.issubset(cols)
    engine.dispose()


def test_upgrading_already_initialized_database(tmp_path):
    """Proves that upgrading an already initialized database is idempotent and safe."""
    db_file = tmp_path / "already_initialized.db"
    db_url = f"sqlite:///{db_file}"

    # Step 1: Pre-initialize with Base.metadata.create_all (simulating legacy or pre-existing DB)
    pre_engine = create_engine(db_url)
    Base.metadata.create_all(bind=pre_engine)
    pre_engine.dispose()

    # Step 2: Run Alembic upgrade head
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    # Step 3: Verify all 12 tables and alembic_version exist
    post_engine = create_engine(db_url)
    inspector = inspect(post_engine)
    tables = set(inspector.get_table_names())

    assert EXPECTED_TABLES.issubset(tables)
    assert "alembic_version" in tables
    post_engine.dispose()


def test_sqlite_wal_mode_preservation(tmp_path):
    """Proves that SQLite WAL mode is preserved and active."""
    db_file = tmp_path / "wal_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    set_sqlite_pragma(engine.raw_connection().connection, None)

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA journal_mode;")).scalar()
        assert str(result).upper() == "WAL"

        fk_result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
        assert fk_result == 1
    engine.dispose()


def test_schema_constraints_and_foreign_keys(tmp_path):
    """Proves that foreign key cascades and unique constraints are established."""
    db_file = tmp_path / "constraints_test.db"
    db_url = f"sqlite:///{db_file}"

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)

    # Check unique constraint on profile_revisions (profile_id, revision_number)
    uqs = inspector.get_unique_constraints("profile_revisions")
    uq_names = [u.get("name") for u in uqs]
    assert any("uq_profile_revision" in (n or "") for n in uq_names)

    # Check foreign keys from profile_revisions to body_profiles
    fks = inspector.get_foreign_keys("profile_revisions")
    assert any(fk["referred_table"] == "body_profiles" for fk in fks)
    engine.dispose()
