r"""
WearWise Development/Staging Admin Account Provisioning Script
==============================================================
Creates or updates the admin account (`admin@wearwise.com`) with a PBKDF2-hashed
password. Defaults to `123456` ONLY in non-production when DEV_ADMIN_PASSWORD
is not provided. Production deployments MUST pass a strong password and rotate
any development credentials.

Usage:
    cd backend
    ..\WEARWISE-BODY-ENGINE\.venv-anny\Scripts\python.exe scripts/seed_admin.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import database as db
from app.config import APP_ENV
from app.core.security import hash_password


def provision_admin() -> dict:
    is_prod = APP_ENV.lower() == "production" or os.getenv("WEARWISE_ENV", "").lower() == "production"
    email = os.getenv("ADMIN_EMAIL", "admin@wearwise.com").lower().strip()
    password = os.getenv("DEV_ADMIN_PASSWORD", "" if is_prod else "123456")

    if not password:
        raise RuntimeError("DEV_ADMIN_PASSWORD / ADMIN_PASSWORD must be explicitly provided in production.")

    if password == "123456":
        print("[WARNING] Using development-only demo password for admin@wearwise.com. Rotate before any production deployment!")

    now_iso = datetime.now(timezone.utc).isoformat()
    existing = db.find_one("users", email=email)
    pw_hash = hash_password(password)

    if existing:
        db.update_one(
            "users",
            {"email": email},
            {
                "password_hash": pw_hash,
                "role": "admin",
                "status": "active",
                "is_active": True,
                "seller_approved": False,
                "requires_password_rotation": password == "123456",
                "updatedAt": now_iso,
            },
        )
        print(f"Updated admin account: {email} (role=admin, PBKDF2-HMAC-SHA256 hashed)")
        return {"action": "updated", "email": email}

    doc = {
        "id": "adm-dev-002",
        "name": "WearWise Administrator",
        "email": email,
        "password_hash": pw_hash,
        "role": "admin",
        "status": "active",
        "is_active": True,
        "seller_approved": False,
        "requires_password_rotation": password == "123456",
        "createdAt": now_iso,
    }
    db.insert("users", doc)
    print(f"Created admin account: {email} (role=admin, PBKDF2-HMAC-SHA256 hashed)")
    return {"action": "created", "email": email}


if __name__ == "__main__":
    provision_admin()
