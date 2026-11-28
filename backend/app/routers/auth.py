"""
Auth router — Role-Aware Commerce & Portal Authentication
=========================================================
POST  /api/auth/signup             — register a new shopper (role strictly 'shopper')
POST  /api/auth/register           — alias for shopper registration
POST  /api/auth/login              — shopper login (rejects seller accounts cleanly)
POST  /api/auth/seller/login       — seller login (rejects shoppers, pending, and suspended accounts)
POST  /api/auth/seller/apply       — non-privileged seller onboarding application (pending admin approval)
POST  /api/auth/admin/login        — admin portal login
POST  /api/auth/logout             — revokes server session and clears HTTP-only auth cookies
GET   /api/auth/me                 — fetch current authenticated user (cookie or Bearer)
PATCH /api/auth/profile            — update shopper onboarding/style profile (shopper only)
GET   /api/auth/admin/sellers      — list seller accounts (admin only)
POST  /api/auth/admin/sellers      — provision an approved seller account (admin only)
PATCH /api/auth/admin/sellers/{id} — approve/suspend seller account (admin only)
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from app import database as db
from app.core.security import (
    clear_auth_cookies,
    create_session_token,
    ensure_auth_seed_and_migration,
    hash_password,
    normalize_user_record,
    require_admin,
    require_authenticated_user,
    require_shopper,
    revoke_token_session,
    sanitize_user_for_client,
    set_auth_cookies,
    verify_password,
    _extract_token_from_request,
)
from app.schemas.auth import (
    AdminCreateSellerRequest,
    LoginRequest,
    ProfileUpdateRequest,
    SellerApplyRequest,
    SellerStatusUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or f"store-{uuid.uuid4().hex[:6]}"


def _issue_session_response(user: dict, response: Response) -> TokenResponse:
    token, csrf_token = create_session_token(user)
    set_auth_cookies(response, token, csrf_token)
    return TokenResponse(
        access_token=token,
        csrf_token=csrf_token,
        user=UserResponse(**sanitize_user_for_client(user)),
    )


def _register_shopper_impl(payload: SignupRequest, response: Response) -> TokenResponse:
    ensure_auth_seed_and_migration()
    email = payload.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email address is required")
    if len(payload.password or "") < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = db.find_one("users", email=email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = {
        "id": str(uuid.uuid4())[:12],
        "name": payload.name.strip() or "WearWise Shopper",
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "shopper",
        "status": "active",
        "is_active": True,
        "seller_approved": False,
        "gender": None,
        "bodyType": None,
        "kidsGender": None,
        "ageGroup": None,
        "onboardingDone": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("users", user)
    return _issue_session_response(user, response)


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, response: Response):
    """Register a new shopper account. Public registration never grants seller or admin roles."""
    return _register_shopper_impl(payload, response)


@router.post("/register", response_model=TokenResponse)
def register(payload: SignupRequest, response: Response):
    """Register a new shopper account (`/register` alias)."""
    return _register_shopper_impl(payload, response)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response):
    """Authenticate a shopper account for the Shopper Portal."""
    ensure_auth_seed_and_migration()
    raw_user = db.find_one("users", email=payload.email.lower().strip())
    if not raw_user or not verify_password(payload.password, raw_user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = normalize_user_record(raw_user)
    if user["role"] == "seller":
        raise HTTPException(
            status_code=403,
            detail="This is a seller account. Please use Seller Login.",
        )
    if user["role"] == "admin":
        raise HTTPException(
            status_code=403,
            detail="This is an administrator account. Please use Admin Login.",
        )
    if user["role"] != "shopper":
        raise HTTPException(
            status_code=403,
            detail="This account cannot sign in through Shopper Login.",
        )
    if not user["is_active"] or user["status"] != "active":
        raise HTTPException(status_code=403, detail="This shopper account is currently inactive.")

    return _issue_session_response(user, response)


@router.post("/seller/login", response_model=TokenResponse)
def seller_login(payload: LoginRequest, response: Response):
    """Authenticate an approved active seller account for the Seller Portal."""
    ensure_auth_seed_and_migration()
    raw_user = db.find_one("users", email=payload.email.lower().strip())
    if not raw_user or not verify_password(payload.password, raw_user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid seller email or password")

    user = normalize_user_record(raw_user)
    if user["role"] == "shopper":
        raise HTTPException(
            status_code=403,
            detail="This account is registered as a shopper. Please use Shopper Login or contact WearWise about seller access.",
        )
    if user["role"] != "seller":
        raise HTTPException(
            status_code=403,
            detail="Seller account credentials required for Seller Portal.",
        )
    if user["status"] == "rejected":
        reason = user.get("rejection_reason")
        detail = "Your seller application was not approved."
        if reason:
            detail += f" Reason: {reason}"
        detail += " You can submit an updated seller application."
        raise HTTPException(status_code=403, detail=detail)
    if not user["seller_approved"] or user["status"] == "pending":
        raise HTTPException(
            status_code=403,
            detail="Your seller account is pending approval by WearWise. Access will open once approved.",
        )
    if not user["is_active"] or user["status"] == "suspended":
        raise HTTPException(
            status_code=403,
            detail="This seller account is currently suspended or inactive.",
        )

    return _issue_session_response(user, response)


@router.post("/seller/apply")
def apply_for_seller(payload: SellerApplyRequest):
    """
    Accepts a non-privileged seller onboarding request.
    Never grants active seller permissions or logs in without WearWise admin approval.
    Permits re-application only for previously rejected seller applications with valid password.
    """
    ensure_auth_seed_and_migration()
    email = payload.email.lower().strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid business email is required")
    if len(payload.password or "") < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    store_name = payload.store_name.strip()
    if len(store_name) < 2:
        raise HTTPException(status_code=400, detail="Store name is required")

    now_iso = datetime.now(timezone.utc).isoformat()
    owner_name = (payload.owner_name or payload.name or store_name).strip()

    existing = db.find_one("users", email=email)
    if existing:
        existing_norm = normalize_user_record(existing)
        if existing_norm["role"] == "seller" and existing_norm["status"] == "rejected":
            if not verify_password(payload.password, existing.get("password_hash", "")):
                raise HTTPException(status_code=403, detail="Please enter the password for your previous application to resubmit.")
            db.update_one(
                "users",
                {"id": existing["id"]},
                {
                    "name": owner_name,
                    "owner_name": owner_name,
                    "store_name": store_name,
                    "store_slug": _slugify(store_name),
                    "phone": (payload.phone or "").strip() or None,
                    "business_type": (payload.business_type or "Apparel Brand").strip(),
                    "business_address": (payload.business_address or "").strip() or None,
                    "store_description": (payload.store_description or "").strip(),
                    "status": "pending",
                    "is_active": False,
                    "seller_approved": False,
                    "rejection_reason": None,
                    "updatedAt": now_iso,
                },
            )
            return {
                "status": "pending_approval",
                "message": "Your updated seller application has been resubmitted and is under review.",
                "email": email,
                "store_name": store_name,
            }
        raise HTTPException(status_code=409, detail="An account or application with this email already exists")

    pending_seller = {
        "id": f"slr-{uuid.uuid4().hex[:8]}",
        "name": owner_name,
        "owner_name": owner_name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "seller",
        "status": "pending",
        "is_active": False,
        "seller_approved": False,
        "brand_id": str(uuid.uuid4()),
        "store_name": store_name,
        "store_slug": _slugify(store_name),
        "phone": (payload.phone or "").strip() or None,
        "business_email": email,
        "business_type": (payload.business_type or "Apparel Brand").strip(),
        "business_address": (payload.business_address or "").strip() or None,
        "store_description": (payload.store_description or "").strip(),
        "brand_tagline": "",
        "rejection_reason": None,
        "createdAt": now_iso,
    }
    db.insert("users", pending_seller)
    return {
        "status": "pending_approval",
        "message": "Your seller application has been recorded and is awaiting WearWise approval. Seller accounts must be approved by WearWise before signing in.",
        "email": email,
        "store_name": store_name,
    }


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, response: Response):
    """Authenticate an active administrator account."""
    ensure_auth_seed_and_migration()
    raw_user = db.find_one("users", email=payload.email.lower().strip())
    if not raw_user or not verify_password(payload.password, raw_user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    user = normalize_user_record(raw_user)
    if user["role"] != "admin" or not user["is_active"] or user["status"] != "active":
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return _issue_session_response(user, response)


@router.post("/logout")
def logout(request: Request, response: Response, authorization: Optional[str] = Header(default=None)):
    """Invalidates the server session (revokes JWT `jti`) and clears HTTP-only auth cookies."""
    raw_token, _ = _extract_token_from_request(request, authorization, enforce_cookie_csrf=False)
    if raw_token:
        revoke_token_session(raw_token)
    clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(require_authenticated_user)):
    """Return the authenticated active user (resolved via HTTP-only cookie or Bearer JWT)."""
    return UserResponse(**sanitize_user_for_client(current_user))


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(require_shopper),
):
    """Update shopper gender, body type and onboarding flags. Never modifies role or permissions."""
    valid_genders = {"men", "women", "kids", None}
    if payload.gender not in valid_genders:
        raise HTTPException(status_code=400, detail="gender must be men, women or kids")

    updates = payload.model_dump(exclude_none=True)
    updated = db.update_one("users", {"id": current_user["id"]}, updates) or current_user
    return UserResponse(**sanitize_user_for_client(updated))


@router.get("/admin/sellers", response_model=list[UserResponse])
def list_sellers(admin_user: dict = Depends(require_admin)):
    """Lists all seller accounts and pending applications (admin only)."""
    ensure_auth_seed_and_migration()
    sellers = [
        UserResponse(**sanitize_user_for_client(u))
        for u in db.find_all("users")
        if (u.get("role") or "shopper") == "seller"
    ]
    return sellers


@router.post("/admin/sellers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_seller(payload: AdminCreateSellerRequest, admin_user: dict = Depends(require_admin)):
    """Provisions a seller account directly (admin only)."""
    ensure_auth_seed_and_migration()
    email = payload.email.lower().strip()
    if db.find_one("users", email=email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if len(payload.password or "") < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    store_name = payload.store_name.strip()
    approved = bool(payload.approved)
    seller_doc = {
        "id": f"slr-{uuid.uuid4().hex[:8]}",
        "name": payload.name.strip() or store_name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": "seller",
        "status": "active" if approved else "pending",
        "is_active": approved,
        "seller_approved": approved,
        "brand_id": (payload.brand_id or str(uuid.uuid4())).strip(),
        "store_name": store_name,
        "store_slug": _slugify(store_name),
        "business_email": (payload.business_email or email).strip(),
        "store_description": (payload.store_description or "").strip(),
        "brand_tagline": (payload.brand_tagline or "").strip(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("users", seller_doc)
    return UserResponse(**sanitize_user_for_client(seller_doc))


@router.patch("/admin/sellers/{seller_id}", response_model=UserResponse)
def admin_update_seller_status(
    seller_id: str,
    payload: SellerStatusUpdateRequest,
    admin_user: dict = Depends(require_admin),
):
    """Approves, activates, or suspends a seller account (admin only)."""
    target = db.find_one("users", id=seller_id)
    if not target or (target.get("role") or "shopper") != "seller":
        raise HTTPException(status_code=404, detail="Seller account not found")
    new_status = payload.status.lower().strip()
    if new_status not in {"active", "pending", "rejected", "suspended"}:
        raise HTTPException(status_code=400, detail="Status must be active, pending, rejected, or suspended")

    approved = (
        payload.seller_approved
        if payload.seller_approved is not None
        else (new_status == "active")
    )
    now_iso = datetime.now(timezone.utc).isoformat()
    updates = {
        "status": new_status,
        "is_active": new_status == "active",
        "seller_approved": bool(approved) if new_status == "active" else False,
        "rejection_reason": (payload.rejection_reason or "").strip() or None if new_status == "rejected" else None,
        "verified_at": now_iso if new_status == "active" else target.get("verified_at"),
    }
    updated = db.update_one("users", {"id": seller_id}, updates)
    return UserResponse(**sanitize_user_for_client(updated))
