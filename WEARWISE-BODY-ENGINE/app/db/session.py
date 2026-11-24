"""
WearWise Database Session and Engine Management
Supports SQLite 3 WAL mode with foreign keys enabled, as well as PostgreSQL connection strings.
"""

import os
import sqlite3
from typing import Generator, Optional
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
# Import all models so Base.metadata knows about them
import app.db.models  # noqa: F401


DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "wearwise.db"
DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforces SQLite WAL journal mode and foreign key constraints."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def get_engine(database_url: str = DEFAULT_DATABASE_URL):
    """Creates SQLAlchemy engine with appropriate connect args."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        # Make sure directory exists
        db_path = database_url.replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False

    return create_engine(database_url, connect_args=connect_args)


engine = get_engine()
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def run_migrations(db_url: Optional[str] = None) -> None:
    """Executes Alembic migrations up to head on the specified or default database."""
    from alembic.config import Config
    from alembic import command
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    cfg = Config(str(alembic_ini_path))
    target_url = db_url or DEFAULT_DATABASE_URL
    cfg.set_main_option("sqlalchemy.url", target_url)
    command.upgrade(cfg, "head")


def init_db(target_engine=None):
    """Initializes tables in database using Alembic migrations or declarative metadata."""
    eng = target_engine or engine
    # If using default engine, apply Alembic migration baseline
    try:
        run_migrations(str(eng.url))
    except Exception:
        # Fallback to create_all if alembic runner context is unavailable
        Base.metadata.create_all(bind=eng)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding transactional database sessions."""
    db = SessionFactory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
