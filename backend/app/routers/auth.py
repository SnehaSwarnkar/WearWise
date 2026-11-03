"""
Auth router
===========
POST /api/auth/signup   — register a new user
POST /api/auth/login    — log in, receive a token
GET  /api/auth/me       — fetch current user by token
PATCH /api/auth/profile — update gender, bodyType, kidsGender, ageGroup
"""

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
    ProfileUpdateRequest,
)
from app import database as db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ── helpers ────────────────────────────────────────────────────────────────────

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _make_token(user_id: str) -> str:
    """Simple deterministic token: sha256(user_id + secret).
    Swap for JWT in production."""
    return hashlib.sha256(f"wearwise-{user_id}".encode()).hexdigest()


def _user_from_token(token: str) -> dict | None:
    for user in db.find_all("users"):
        if _make_token(user["id"]) == token:
            return user
    return None


def _to_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        gender=user.get("gender"),
        bodyType=user.get("bodyType"),
        kidsGender=user.get("kidsGender"),
        ageGroup=user.get("ageGroup"),
        onboardingDone=user.get("onboardingDone", False),
    )


# ── routes ─────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    """Register a new user."""
    existing = db.find_one("users", email=payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = {
        "id": str(uuid.uuid4())[:12],
        "name": payload.name.strip(),
        "email": payload.email.lower().strip(),
        "password_hash": _hash_pw(payload.password),
        "gender": None,
        "bodyType": None,
        "kidsGender": None,
        "ageGroup": None,
        "onboardingDone": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    db.insert("users", user)

    return TokenResponse(
        access_token=_make_token(user["id"]),
        user=_to_response(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate and return a token."""
    user = db.find_one("users", email=payload.email.lower().strip())
    if not user or user["password_hash"] != _hash_pw(payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(
        access_token=_make_token(user["id"]),
        user=_to_response(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(authorization: str = Header(...)):
    """Return current user from Bearer token."""
    token = authorization.removeprefix("Bearer ").strip()
    user = _user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return _to_response(user)


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    authorization: str = Header(...),
):
    """Update gender, body type and onboarding flags."""
    token = authorization.removeprefix("Bearer ").strip()
    user = _user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    valid_genders = {"men", "women", "kids", None}
    if payload.gender not in valid_genders:
        raise HTTPException(status_code=400, detail="gender must be men, women or kids")

    updates = payload.model_dump(exclude_none=True)
    updated = db.update_one("users", {"id": user["id"]}, updates)
    return _to_response(updated)
