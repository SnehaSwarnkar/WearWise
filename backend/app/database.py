"""
WearWise Database Layer
=======================
Primary database: MongoDB Atlas via PyMongo (single cluster, logical database: wearwise_commerce).
Includes automatic connection verification, connection pooling, and resilient JSON-file fallback
for environments where MongoDB is unreachable or unconfigured.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import (
    MONGODB_URI,
    MONGODB_COMMERCE_DB,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
    APP_ENV,
)

logger = logging.getLogger("wearwise.commerce.db")

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_mongo_client: Optional[MongoClient] = None
_mongo_db = None
_use_mongo: Optional[bool] = None


def get_client() -> Optional[MongoClient]:
    global _mongo_client, _mongo_db, _use_mongo
    if _mongo_client is not None:
        return _mongo_client
    if not MONGODB_URI:
        _use_mongo = False
        return None
    try:
        _mongo_client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
            appname="WearWiseCommerce",
        )
        # Test connection
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[MONGODB_COMMERCE_DB]
        _use_mongo = True
        logger.info(f"Connected to MongoDB Atlas database: {MONGODB_COMMERCE_DB}")
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"MongoDB connection failed ({e}). Falling back to JSON file storage.")
        _mongo_client = None
        _mongo_db = None
        _use_mongo = False
    return _mongo_client


def get_db():
    global _mongo_db
    if _mongo_db is None and _use_mongo is not False:
        get_client()
    return _mongo_db


def is_mongo_active() -> bool:
    global _use_mongo
    if _use_mongo is None:
        get_client()
    return bool(_use_mongo and _mongo_db is not None)


def ping() -> dict:
    """Returns database connection status and metadata."""
    if not is_mongo_active():
        return {
            "ok": False,
            "engine": "json_files",
            "database": str(DATA_DIR),
            "status": "fallback_local_json",
        }
    try:
        client = get_client()
        if client:
            client.admin.command("ping")
            collections = _mongo_db.list_collection_names()
            return {
                "ok": True,
                "engine": "mongodb_atlas",
                "database": MONGODB_COMMERCE_DB,
                "collections": collections,
                "status": "connected",
            }
    except Exception as e:
        return {
            "ok": False,
            "engine": "mongodb_atlas",
            "database": MONGODB_COMMERCE_DB,
            "error": str(e),
            "status": "error",
        }
    return {"ok": False, "status": "unknown"}


# ── JSON file fallback helpers ────────────────────────────────────────────────

def _json_path(collection: str) -> Path:
    return DATA_DIR / f"{collection}.json"


def _json_load(collection: str) -> list[dict]:
    p = _json_path(collection)
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _json_save(collection: str, records: list[dict]) -> None:
    with open(_json_path(collection), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)


# ── Universal Database Interface ──────────────────────────────────────────────

def load(collection: str) -> list[dict]:
    return find_all(collection)


def save(collection: str, records: list[dict]) -> None:
    if is_mongo_active():
        db = get_db()
        db[collection].delete_many({})
        if records:
            docs = [{k: v for k, v in r.items() if k != "_id"} for r in records]
            db[collection].insert_many(docs)
    else:
        _json_save(collection, records)


def find_all(collection: str) -> list[dict]:
    if is_mongo_active():
        db = get_db()
        return list(db[collection].find({}, {"_id": 0}))
    return _json_load(collection)


def find_one(collection: str, **kwargs) -> Optional[dict]:
    if is_mongo_active():
        db = get_db()
        return db[collection].find_one(kwargs, {"_id": 0})
    for record in _json_load(collection):
        if all(record.get(k) == v for k, v in kwargs.items()):
            return record
    return None


def insert(collection: str, record: dict) -> dict:
    if is_mongo_active():
        db = get_db()
        doc = dict(record)
        doc.pop("_id", None)
        db[collection].insert_one(doc)
        doc.pop("_id", None)
        return doc
    records = _json_load(collection)
    records.append(record)
    _json_save(collection, records)
    return record


def update_one(collection: str, match: dict, updates: dict) -> Optional[dict]:
    if is_mongo_active():
        db = get_db()
        db[collection].update_one(match, {"$set": updates})
        return db[collection].find_one(match, {"_id": 0})
    records = _json_load(collection)
    for i, record in enumerate(records):
        if all(record.get(k) == v for k, v in match.items()):
            records[i] = {**record, **updates}
            _json_save(collection, records)
            return records[i]
    return None


def delete_one(collection: str, **kwargs) -> bool:
    if is_mongo_active():
        db = get_db()
        res = db[collection].delete_one(kwargs)
        return res.deleted_count > 0
    records = _json_load(collection)
    new_records = [r for r in records if not all(r.get(k) == v for k, v in kwargs.items())]
    if len(new_records) == len(records):
        return False
    _json_save(collection, new_records)
    return True


def filter_by(collection: str, **kwargs) -> list[dict]:
    if is_mongo_active():
        db = get_db()
        return list(db[collection].find(kwargs, {"_id": 0}))
    return [
        r for r in _json_load(collection)
        if all(r.get(k) == v for k, v in kwargs.items())
    ]
