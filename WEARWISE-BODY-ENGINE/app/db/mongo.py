"""
WearWise Body Engine MongoDB Layer
===================================
Manages document persistence and querying on MongoDB Atlas (wearwise_body_engine).
Coordinates with PyMongo driver with connection pooling and resilient health checks.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import (
    MONGODB_URI,
    MONGODB_BODY_ENGINE_DB,
    MONGODB_COMMERCE_DB,
    MONGODB_SERVER_SELECTION_TIMEOUT_MS,
)

logger = logging.getLogger("wearwise.body_engine.mongo")

_mongo_client: Optional[MongoClient] = None
_mongo_db = None
_is_connected: Optional[bool] = None


def get_client() -> Optional[MongoClient]:
    global _mongo_client, _mongo_db, _is_connected
    if _mongo_client is not None:
        return _mongo_client
    if not MONGODB_URI:
        _is_connected = False
        return None
    try:
        _mongo_client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=MONGODB_SERVER_SELECTION_TIMEOUT_MS,
            appname="WearWiseBodyEngine",
        )
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[MONGODB_BODY_ENGINE_DB]
        _is_connected = True
        logger.info(f"Connected to MongoDB Atlas database: {MONGODB_BODY_ENGINE_DB}")
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"Body Engine MongoDB Atlas connection failed ({e}).")
        _mongo_client = None
        _mongo_db = None
        _is_connected = False
    return _mongo_client


def get_db():
    global _mongo_db
    if _mongo_db is None and _is_connected is not False:
        get_client()
    return _mongo_db


def is_active() -> bool:
    global _is_connected
    if _is_connected is None:
        get_client()
    return bool(_is_connected and _mongo_db is not None)


def ping() -> dict:
    """Verifies MongoDB connectivity and returns status metadata."""
    if not is_active():
        return {
            "ok": False,
            "engine": "mongodb_atlas",
            "database": MONGODB_BODY_ENGINE_DB,
            "status": "unconnected",
        }
    try:
        client = get_client()
        if client:
            client.admin.command("ping")
            collections = _mongo_db.list_collection_names()
            return {
                "ok": True,
                "engine": "mongodb_atlas",
                "database": MONGODB_BODY_ENGINE_DB,
                "collections": collections,
                "status": "connected",
            }
    except Exception as e:
        return {
            "ok": False,
            "engine": "mongodb_atlas",
            "database": MONGODB_BODY_ENGINE_DB,
            "error": str(e),
            "status": "error",
        }
    return {"ok": False, "status": "unknown"}


def serialize_doc(data: Any) -> Any:
    """Recursively serializes UUIDs, Decimals, datetimes for MongoDB insertion."""
    if isinstance(data, dict):
        return {k: serialize_doc(v) for k, v in data.items() if k != "_id"}
    elif isinstance(data, list):
        return [serialize_doc(item) for item in data]
    elif isinstance(data, UUID):
        return str(data)
    elif isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


def get_collection(name: str):
    db = get_db()
    if db is not None:
        return db[name]
    return None


def get_commerce_db():
    client = get_client()
    if client is not None and is_active():
        return client[MONGODB_COMMERCE_DB]
    return None


def get_commerce_collection(name: str):
    cdb = get_commerce_db()
    if cdb is not None:
        return cdb[name]
    return None


# ── MongoDB Document Repository Operations ────────────────────────────────────

def upsert_document(collection_name: str, filter_query: Dict[str, Any], doc: Dict[str, Any]) -> bool:
    if not is_active():
        return False
    try:
        col = get_collection(collection_name)
        if col is not None:
            clean_doc = serialize_doc(doc)
            col.update_one(filter_query, {"$set": clean_doc}, upsert=True)
            return True
    except Exception as e:
        logger.error(f"MongoDB upsert error in {collection_name}: {e}")
    return False


def update_document(collection_name: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
    if not is_active():
        return False
    try:
        col = get_collection(collection_name)
        if col is not None:
            if not any(k.startswith("$") for k in update_data.keys()):
                update_op = {"$set": serialize_doc(update_data)}
            else:
                update_op = update_data
            col.update_one(filter_query, update_op)
            return True
    except Exception as e:
        logger.error(f"MongoDB update error in {collection_name}: {e}")
    return False


def find_document(collection_name: str, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not is_active():
        return None
    try:
        col = get_collection(collection_name)
        if col is not None:
            doc = col.find_one(filter_query, {"_id": 0})
            return doc
    except Exception as e:
        logger.error(f"MongoDB find_one error in {collection_name}: {e}")
    return None


def find_documents(collection_name: str, filter_query: Dict[str, Any], sort_field: Optional[str] = None, ascending: bool = True, limit: int = 100) -> List[Dict[str, Any]]:
    if not is_active():
        return []
    try:
        col = get_collection(collection_name)
        if col is not None:
            cursor = col.find(filter_query, {"_id": 0})
            if sort_field:
                direction = pymongo.ASCENDING if ascending else pymongo.DESCENDING
                cursor = cursor.sort(sort_field, direction)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
    except Exception as e:
        logger.error(f"MongoDB find error in {collection_name}: {e}")
    return []


def delete_document(collection_name: str, filter_query: Dict[str, Any]) -> bool:
    if not is_active():
        return False
    try:
        col = get_collection(collection_name)
        if col is not None:
            res = col.delete_one(filter_query)
            return res.deleted_count > 0
    except Exception as e:
        logger.error(f"MongoDB delete error in {collection_name}: {e}")
    return False
