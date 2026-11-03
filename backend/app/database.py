"""
Lightweight JSON-file database.
Keeps each collection in its own file inside backend/data/.
No external DB required — swap to a real DB by replacing the functions here.
"""

import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _path(collection: str) -> Path:
    return DATA_DIR / f"{collection}.json"


def load(collection: str) -> list[dict]:
    p = _path(collection)
    if not p.exists():
        return []
    with open(p, "r") as f:
        return json.load(f)


def save(collection: str, records: list[dict]) -> None:
    with open(_path(collection), "w") as f:
        json.dump(records, f, indent=2, default=str)


def find_all(collection: str) -> list[dict]:
    return load(collection)


def find_one(collection: str, **kwargs) -> dict | None:
    for record in load(collection):
        if all(record.get(k) == v for k, v in kwargs.items()):
            return record
    return None


def insert(collection: str, record: dict) -> dict:
    records = load(collection)
    records.append(record)
    save(collection, records)
    return record


def update_one(collection: str, match: dict, updates: dict) -> dict | None:
    records = load(collection)
    for i, record in enumerate(records):
        if all(record.get(k) == v for k, v in match.items()):
            records[i] = {**record, **updates}
            save(collection, records)
            return records[i]
    return None


def delete_one(collection: str, **kwargs) -> bool:
    records = load(collection)
    new_records = [r for r in records if not all(r.get(k) == v for k, v in kwargs.items())]
    if len(new_records) == len(records):
        return False
    save(collection, new_records)
    return True


def filter_by(collection: str, **kwargs) -> list[dict]:
    return [
        r for r in load(collection)
        if all(r.get(k) == v for k, v in kwargs.items())
    ]
