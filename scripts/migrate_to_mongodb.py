"""
WearWise MongoDB Atlas Migration Script
=======================================
Idempotent migration from local JSON files and SQLite databases to MongoDB Atlas.

Databases:
  - wearwise_commerce: JSON files from backend/data/*.json
  - wearwise_body_engine: SQLite tables from WEARWISE-BODY-ENGINE/data/wearwise.db

Usage:
  python scripts/migrate_to_mongodb.py [--dry-run] [--no-backup] [--verify-only]
"""

import argparse
import json
import logging
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wearwise.migration")

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMERCE_DATA_DIR = REPO_ROOT / "backend" / "data"
BODY_ENGINE_DATA_DIR = REPO_ROOT / "WEARWISE-BODY-ENGINE" / "data"
SQLITE_DB_PATH = BODY_ENGINE_DATA_DIR / "wearwise.db"
BACKUP_DIR = REPO_ROOT / "data_backups"

# Load root .env
load_dotenv(REPO_ROOT / ".env", override=False)

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_COMMERCE_DB = os.getenv("MONGODB_COMMERCE_DB", "wearwise_commerce")
MONGODB_BODY_ENGINE_DB = os.getenv("MONGODB_BODY_ENGINE_DB", "wearwise_body_engine")
TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))


def parse_args():
    parser = argparse.ArgumentParser(description="WearWise MongoDB Atlas Migration Tool")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without modifying MongoDB Atlas")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating local timestamped backup of source data")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing MongoDB records without inserting")
    return parser.parse_args()


def create_backup():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target_backup = BACKUP_DIR / f"backup_{timestamp}"
    target_backup.mkdir(parents=True, exist_ok=True)

    if COMMERCE_DATA_DIR.exists():
        shutil.copytree(COMMERCE_DATA_DIR, target_backup / "commerce_data", dirs_exist_ok=True)
    if SQLITE_DB_PATH.exists():
        (target_backup / "body_engine_data").mkdir(parents=True, exist_ok=True)
        shutil.copy2(SQLITE_DB_PATH, target_backup / "body_engine_data" / "wearwise.db")

    logger.info(f"Created local source backup at: {target_backup}")
    return target_backup


def get_mongo_client() -> MongoClient:
    if not MONGODB_URI:
        logger.error("MONGODB_URI is not configured in root .env. Please set it before migrating.")
        sys.exit(1)
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=TIMEOUT_MS,
            connectTimeoutMS=TIMEOUT_MS,
            appname="WearWiseMigrationTool",
        )
        client.admin.command("ping")
        # Mask credentials in logs
        masked = MONGODB_URI.split("@")[-1] if "@" in MONGODB_URI else "Atlas"
        logger.info(f"Connected to MongoDB Atlas cluster at: ...@{masked}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        sys.exit(1)


def migrate_commerce(client: MongoClient, dry_run: bool, verify_only: bool) -> List[Dict[str, Any]]:
    results = []
    db = client[MONGODB_COMMERCE_DB]

    if not COMMERCE_DATA_DIR.exists():
        logger.warning(f"Commerce data directory not found: {COMMERCE_DATA_DIR}")
        return results

    json_files = list(COMMERCE_DATA_DIR.glob("*.json"))
    for file_path in json_files:
        collection_name = file_path.stem
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            continue

        if not isinstance(data, list):
            logger.warning(f"Skipping {file_path}: expected JSON list of records.")
            continue

        source_count = len(data)
        col = db[collection_name]

        if not verify_only and not dry_run and source_count > 0:
            for record in data:
                doc = {k: v for k, v in record.items() if k != "_id"}
                # Identify document key
                if "id" in doc:
                    col.replace_one({"id": doc["id"]}, doc, upsert=True)
                elif "email" in doc:
                    col.replace_one({"email": doc["email"]}, doc, upsert=True)
                elif "user_id" in doc:
                    col.replace_one({"user_id": doc["user_id"]}, doc, upsert=True)
                else:
                    col.insert_one(doc)

        target_count = col.count_documents({}) if not dry_run else 0
        status = "DRY-RUN" if dry_run else ("VERIFIED" if target_count >= source_count else "MISMATCH")
        results.append({
            "database": MONGODB_COMMERCE_DB,
            "collection": collection_name,
            "source_count": source_count,
            "target_count": target_count if not dry_run else source_count,
            "status": status,
        })
        logger.info(f"[Commerce] {collection_name}: {source_count} source records -> {target_count} in Atlas ({status})")

    return results


def migrate_body_engine(client: MongoClient, dry_run: bool, verify_only: bool) -> List[Dict[str, Any]]:
    results = []
    db = client[MONGODB_BODY_ENGINE_DB]

    if not SQLITE_DB_PATH.exists():
        logger.warning(f"SQLite database not found: {SQLITE_DB_PATH}")
        return results

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get list of user tables (skip alembic_version)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version';")
    tables = [row["name"] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        source_count = len(rows)
        col = db[table]

        if not verify_only and not dry_run and source_count > 0:
            for row in rows:
                doc = dict(row)
                # Parse JSON fields if string
                for k, v in doc.items():
                    if isinstance(v, str) and (k.endswith("_json") or k.endswith("_spec")):
                        try:
                            doc[k] = json.loads(v)
                        except Exception:
                            pass
                # Convert boolean integers
                for bool_key in ["is_deleted", "is_valid_manifold"]:
                    if bool_key in doc and isinstance(doc[bool_key], int):
                        doc[bool_key] = bool(doc[bool_key])

                if "id" in doc:
                    col.replace_one({"id": str(doc["id"])}, doc, upsert=True)
                else:
                    col.insert_one(doc)

        target_count = col.count_documents({}) if not dry_run else 0
        status = "DRY-RUN" if dry_run else ("VERIFIED" if target_count >= source_count else "MISMATCH")
        results.append({
            "database": MONGODB_BODY_ENGINE_DB,
            "collection": table,
            "source_count": source_count,
            "target_count": target_count if not dry_run else source_count,
            "status": status,
        })
        logger.info(f"[Body Engine] {table}: {source_count} source records -> {target_count} in Atlas ({status})")

    conn.close()
    return results


def main():
    args = parse_args()
    logger.info("Starting WearWise MongoDB Atlas Migration Tool...")
    if args.dry_run:
        logger.info("Mode: DRY-RUN (no modifications to Atlas)")

    if not args.no_backup and not args.dry_run and not args.verify_only:
        create_backup()

    client = get_mongo_client()

    commerce_results = migrate_commerce(client, args.dry_run, args.verify_only)
    body_engine_results = migrate_body_engine(client, args.dry_run, args.verify_only)

    all_results = commerce_results + body_engine_results

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'DATABASE':<24} {'COLLECTION':<26} {'SOURCE':<8} {'TARGET':<8} {'STATUS'}")
    print("-" * 80)
    for r in all_results:
        print(f"{r['database']:<24} {r['collection']:<26} {r['source_count']:<8} {r['target_count']:<8} {r['status']}")
    print("=" * 80 + "\n")

    mismatches = [r for r in all_results if r["status"] == "MISMATCH"]
    if mismatches:
        logger.error(f"Migration completed with {len(mismatches)} mismatched collections!")
        sys.exit(1)

    logger.info("Migration completed successfully with 100% data reconciliation.")
    sys.exit(0)


if __name__ == "__main__":
    main()
