"""
WearWise Commerce Authentication, Session & RBAC Security Layer
==============================================================
Provides:
- Server-authoritative roles (`shopper`, `seller`, `admin`) and active/approval status checks
- Salted PBKDF2 password hashing (with safe legacy SHA-256 verification for existing test records)
- Shared signed HS256 JWT tokens compatible with WEARWISE-BODY-ENGINE
- HTTP-only session cookies + double-submit CSRF protection + Bearer header compatibility
- Server-side session revocation on logout (`auth_sessions`)
- Idempotent safe migration of existing users and staging portal seed accounts
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import Cookie, Header, HTTPException, Request, Response, status

from app import database as db
from app.config import APP_ENV

VALID_ROLES = {"shopper", "seller", "admin"}
VALID_STATUSES = {"active", "pending", "suspended"}

AUTH_COOKIE_NAME = "ww_auth_session"
CSRF_COOKIE_NAME = "ww_csrf_token"
CANONICAL_DEFAULT_BRAND_ID = "e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e"
CANONICAL_SECOND_BRAND_ID = "f7a1c3d2-4e5b-4a8c-9d1e-2b3c4d5e6f70"

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "wearwise-dev-signing-key-for-local-testing-only-32bytes",
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "wearwise:auth")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "wearwise:api")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "240"))

IS_PRODUCTION = APP_ENV.lower() == "production" or os.getenv("WEARWISE_ENV", "").lower() == "production"
UNSAFE_HTTP_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_MIGRATION_DONE = False


def hash_password(password: str) -> str:
    """Hashes a plaintext password with per-user salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies PBKDF2 salted hashes cleanly, plus legacy unsalted SHA-256 test/migration hashes."""
    if not stored_hash:
        return False
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$", 2)
        if len(parts) != 3:
            return False
        _, salt, expected_hex = parts
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return hmac.compare_digest(dk.hex(), expected_hex)
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def derive_body_engine_user_id(user_id: str) -> str:
    """Deterministic UUID derivation matching frontend/Body Engine principal convention."""
    sanitized = "".join(ch for ch in str(user_id) if ch.isalnum()).ljust(12, "0")[:12].lower()
    return f"c1f7a28e-8e3b-48d9-a791-{sanitized}"


def normalize_user_record(user: dict[str, Any]) -> dict[str, Any]:
    """Ensures every user dict has authoritative role, status, and approval defaults."""
    role = str(user.get("role") or "shopper").lower()
    if role not in VALID_ROLES:
        role = "shopper"
    user_status = str(user.get("status") or "active").lower()
    if user_status not in VALID_STATUSES:
        user_status = "active"
    is_active = bool(user.get("is_active", user_status == "active"))
    seller_approved = bool(user.get("seller_approved", role == "seller" and user_status == "active"))
    return {
        **user,
        "role": role,
        "status": user_status,
        "is_active": is_active,
        "seller_approved": seller_approved,
    }


def sanitize_user_for_client(user: dict[str, Any]) -> dict[str, Any]:
    """Strips secret fields and exposes safe account metadata."""
    u = normalize_user_record(user)
    return {
        "id": u["id"],
        "name": u["name"],
        "email": u["email"],
        "role": u["role"],
        "status": u["status"],
        "is_active": u["is_active"],
        "seller_approved": u["seller_approved"],
        "brand_id": u.get("brand_id"),
        "store_name": u.get("store_name"),
        "store_slug": u.get("store_slug"),
        "business_email": u.get("business_email"),
        "store_description": u.get("store_description"),
        "brand_tagline": u.get("brand_tagline"),
        "gender": u.get("gender"),
        "bodyType": u.get("bodyType"),
        "kidsGender": u.get("kidsGender"),
        "ageGroup": u.get("ageGroup"),
        "onboardingDone": bool(u.get("onboardingDone", False)),
        "createdAt": u.get("createdAt"),
    }


def create_session_token(user: dict[str, Any]) -> tuple[str, str]:
    """
    Mints a revocable HS256 JWT token signed with the shared WearWise key and registers `jti`.
    Returns `(jwt_token, csrf_token)`.
    """
    u = normalize_user_record(user)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=JWT_EXPIRY_MINUTES)
    jti = uuid.uuid4().hex
    csrf_token = secrets.token_urlsafe(24)

    role = u["role"]
    if role == "seller":
        principal_type = "brand"
        subject = str(u.get("brand_id") or CANONICAL_DEFAULT_BRAND_ID)
    elif role == "admin":
        principal_type = "admin"
        subject = str(u["id"])
    else:
        principal_type = "shopper"
        subject = derive_body_engine_user_id(u["id"])

    claims: dict[str, Any] = {
        "sub": str(u["id"]),
        "commerce_user_id": str(u["id"]),
        "user_id": subject if role != "seller" else str(u["id"]),
        "principal_type": principal_type,
        "role": role,
        "jti": jti,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    if role == "seller":
        claims["brand_id"] = str(u.get("brand_id") or CANONICAL_DEFAULT_BRAND_ID)

    token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    db.insert(
        "auth_sessions",
        {
            "jti": jti,
            "user_id": u["id"],
            "role": role,
            "revoked": False,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        },
    )
    return token, csrf_token


def set_auth_cookies(response: Response, token: str, csrf_token: str) -> None:
    """Attaches HTTP-only auth cookie + readable CSRF double-submit cookie."""
    max_age = JWT_EXPIRY_MINUTES * 60
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=IS_PRODUCTION,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        samesite="lax",
        secure=IS_PRODUCTION,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clears auth and CSRF cookies cleanly on logout."""
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


def revoke_token_session(raw_token: str) -> None:
    """Marks the JWT session `jti` as revoked in `auth_sessions`."""
    if not raw_token:
        return
    try:
        claims = jwt.decode(
            raw_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"verify_exp": False},
        )
        jti = claims.get("jti")
        if jti:
            existing = db.find_one("auth_sessions", jti=jti)
            now_iso = datetime.now(timezone.utc).isoformat()
            if existing:
                db.update_one("auth_sessions", {"jti": jti}, {"revoked": True, "revoked_at": now_iso})
            else:
                db.insert(
                    "auth_sessions",
                    {
                        "jti": jti,
                        "user_id": claims.get("commerce_user_id") or claims.get("sub"),
                        "role": claims.get("role", "shopper"),
                        "revoked": True,
                        "revoked_at": now_iso,
                    },
                )
    except jwt.PyJWTError:
        pass


def _decode_and_validate_token(raw_token: str) -> Optional[dict[str, Any]]:
    """
    Resolves either:
    1) Signed WearWise JWT (checking signature, expiry, issuer, audience, and revocation), OR
    2) Legacy M5 deterministic sha256('wearwise-' + user_id) token (strictly non-production compat).
    """
    if not raw_token:
        return None
    if "." in raw_token:
        try:
            claims = jwt.decode(
                raw_token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                issuer=JWT_ISSUER,
                audience=JWT_AUDIENCE,
                options={"require": ["exp", "iss", "aud", "sub"], "verify_exp": True},
            )
        except jwt.PyJWTError:
            return None

        jti = claims.get("jti")
        if jti:
            sess = db.find_one("auth_sessions", jti=jti)
            if sess and sess.get("revoked"):
                return None

        uid = claims.get("commerce_user_id") or claims.get("sub")
        user = db.find_one("users", id=uid)
        if not user:
            return None
        return normalize_user_record(user)

    if not IS_PRODUCTION:
        for u in db.find_all("users"):
            legacy_tok = hashlib.sha256(f"wearwise-{u['id']}".encode("utf-8")).hexdigest()
            if hmac.compare_digest(legacy_tok, raw_token):
                return normalize_user_record(u)
    return None


def _extract_token_from_request(
    request: Request,
    authorization: Optional[str] = None,
    enforce_cookie_csrf: bool = True,
) -> tuple[Optional[str], bool]:
    """
    Extracts `(raw_token, used_cookie)` giving explicit Bearer headers priority over cookies.
    Enforces CSRF double-submit check on unsafe cookie-authenticated HTTP methods.
    """
    auth_hdr = authorization or request.headers.get("authorization")
    if auth_hdr:
        parts = auth_hdr.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
            return parts[1].strip(), False
        return auth_hdr.strip(), False

    cookie_tok = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_tok:
        if enforce_cookie_csrf and request.method.upper() in UNSAFE_HTTP_METHODS:
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
            csrf_header = request.headers.get("x-csrf-token")
            if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF verification failed. Refresh the page and try again.",
                )
        return cookie_tok.strip(), True

    return None, False


def get_optional_authenticated_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> Optional[dict[str, Any]]:
    """
    Returns authenticated user when credentials are supplied; returns None when anonymous.
    Raises 401 if an explicit invalid/revoked Bearer token was supplied.
    """
    raw_token, used_cookie = _extract_token_from_request(request, authorization, enforce_cookie_csrf=True)
    if not raw_token:
        return None
    user = _decode_and_validate_token(raw_token)
    if not user:
        if used_cookie:
            return None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not user["is_active"] or user["status"] != "active":
        if used_cookie:
            return None
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive or suspended.")
    return user


def require_authenticated_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Strict authentication dependency returning the normalized active user or raising 401/403."""
    raw_token, _ = _extract_token_from_request(request, authorization, enforce_cookie_csrf=True)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = _decode_and_validate_token(raw_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    if not user["is_active"] or user["status"] == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive or suspended.")
    return user


def require_shopper(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Requires an active `shopper` account (rejects seller/admin accounts with 403)."""
    user = require_authenticated_user(request, authorization)
    if user["role"] != "shopper":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shopper account required for this action.",
        )
    return user


def reject_seller_portal_access(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> None:
    """Blocks authenticated seller accounts from shopper-only endpoints while permitting shoppers and guests."""
    user = get_optional_authenticated_user(request, authorization)
    if user and user.get("role") == "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller accounts cannot access shopper-only wardrobe, style, or wishlist features.",
        )


def require_active_seller(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Requires an active, approved `seller` account with a valid `brand_id`."""
    user = require_authenticated_user(request, authorization)
    if user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller privileges required.",
        )
    if not user.get("seller_approved") or user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account is pending WearWise approval or inactive.",
        )
    if not user.get("brand_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller store brand identifier is missing.",
        )
    return user


def require_admin(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Requires an active `admin` account."""
    user = require_authenticated_user(request, authorization)
    if user["role"] != "admin" or user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )
    return user


def ensure_auth_seed_and_migration(force: bool = False) -> dict[str, int]:
    """
    Safely migrates legacy user records (assigning `role='shopper'` without resetting data)
    and idempotently seeds staging seller/shopper/admin accounts in non-production environments.
    """
    global _MIGRATION_DONE
    if _MIGRATION_DONE and not force:
        return {"migrated": 0, "seeded": 0}

    migrated = 0
    for user in db.find_all("users"):
        updates: dict[str, Any] = {}
        if "role" not in user or not user.get("role"):
            updates["role"] = "shopper"
        if "status" not in user or not user.get("status"):
            updates["status"] = "active"
        if "is_active" not in user:
            updates["is_active"] = updates.get("status", user.get("status", "active")) == "active"
        if "seller_approved" not in user:
            eff_role = updates.get("role", user.get("role", "shopper"))
            updates["seller_approved"] = eff_role == "seller" and updates.get("is_active", True)
        if updates:
            db.update_one("users", {"id": user["id"]}, updates)
            migrated += 1

    seeded = 0
    if not IS_PRODUCTION:
        now_iso = datetime.now(timezone.utc).isoformat()
        seller_pw = os.getenv("SEED_SELLER_PASSWORD", "WearWiseSeller#2026")
        shopper_pw = os.getenv("SEED_SHOPPER_PASSWORD", "WearWiseShopper#2026")
        admin_pw = os.getenv("SEED_ADMIN_PASSWORD", "WearWiseAdmin#2026")

        seed_accounts = [
            {
                "id": "slr-official-001",
                "name": "WearWise Studio Lead",
                "email": "seller@wearwise.studio",
                "password_hash": hash_password(seller_pw),
                "role": "seller",
                "status": "active",
                "is_active": True,
                "seller_approved": True,
                "brand_id": CANONICAL_DEFAULT_BRAND_ID,
                "store_name": "WearWise Official Studio",
                "store_slug": "wearwise-official-studio",
                "business_email": "studio@wearwise.studio",
                "store_description": "Official WearWise staging apparel studio featuring pattern-first 3D garments and editorial essentials.",
                "brand_tagline": "Engineered silhouettes & honest garment sizing.",
                "createdAt": now_iso,
            },
            {
                "id": "slr-studio-002",
                "name": "Atelier Two Merchant",
                "email": "studio.two@wearwise.studio",
                "password_hash": hash_password(seller_pw),
                "role": "seller",
                "status": "active",
                "is_active": True,
                "seller_approved": True,
                "brand_id": CANONICAL_SECOND_BRAND_ID,
                "store_name": "Atelier Two Collective",
                "store_slug": "atelier-two-collective",
                "business_email": "hello@ateliertwo.wearwise.studio",
                "store_description": "Independent womenswear and tailored separates staging storefront.",
                "brand_tagline": "Small-batch tailoring for modern wardrobes.",
                "createdAt": now_iso,
            },
            {
                "id": "slr-pending-003",
                "name": "Pending Applicant",
                "email": "pending.seller@wearwise.studio",
                "password_hash": hash_password(seller_pw),
                "role": "seller",
                "status": "pending",
                "is_active": False,
                "seller_approved": False,
                "brand_id": "a1b2c3d4-0000-4000-8000-000000000099",
                "store_name": "Pending Apparel Co.",
                "store_slug": "pending-apparel-co",
                "business_email": "pending@wearwise.studio",
                "store_description": "Awaiting WearWise merchant verification.",
                "brand_tagline": "Pending verification.",
                "createdAt": now_iso,
            },
            {
                "id": "usr-staging-001",
                "name": "Riya Shopper",
                "email": "shopper@wearwise.test",
                "password_hash": hash_password(shopper_pw),
                "role": "shopper",
                "status": "active",
                "is_active": True,
                "seller_approved": False,
                "gender": "women",
                "onboardingDone": True,
                "createdAt": now_iso,
            },
            {
                "id": "adm-staging-001",
                "name": "WearWise Platform Admin",
                "email": "admin@wearwise.studio",
                "password_hash": hash_password(admin_pw),
                "role": "admin",
                "status": "active",
                "is_active": True,
                "seller_approved": False,
                "createdAt": now_iso,
            },
        ]

        for acc in seed_accounts:
            existing = db.find_one("users", email=acc["email"])
            if not existing:
                db.insert("users", acc)
                seeded += 1

    _MIGRATION_DONE = True
    return {"migrated": migrated, "seeded": seeded}
