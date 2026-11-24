"""
WearWise API Authentication & Ownership Dependencies
Implements replaceable TokenVerifier protocol and JWT signature/issuer/audience/expiry validation.
Strictly distinguishes production mode from development-only identity adapters.
Declares standard Bearer security scheme in OpenAPI.
Never trusts client-supplied user or brand IDs from request bodies.
"""

import time
import uuid
from typing import Optional, Dict, Any, Protocol
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import (
    IS_PRODUCTION,
    ALLOW_DEV_AUTH,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ISSUER,
    JWT_AUDIENCE,
    JWT_EXPIRY_MINUTES,
)


# Canonical demo identities (only available in development when explicitly enabled)
DEFAULT_DEV_USER_ID = uuid.UUID("c1f7a28e-8e3b-48d9-a791-03f4439c1b3e")
DEFAULT_DEV_BRAND_ID = uuid.UUID("e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e")

# FastAPI security scheme declaring Bearer authentication in OpenAPI docs
bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="JWT Bearer Token for authenticated User or Merchant Brand principal.",
    auto_error=False,
)


# -----------------------------------------------------------------------------
# Replaceable Token Verifier Protocol & Implementation
# -----------------------------------------------------------------------------

class TokenVerifier(Protocol):
    """
    Abstract token verification interface.
    Enables swapping JWT verification with external identity providers (Auth0, Okta, Keycloak).
    """
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Validates token integrity, signature, issuer, audience, and expiration.
        Returns decoded claims dictionary or raises HTTPException(401).
        """
        ...


class JWTTokenVerifier:
    """
    Default token verifier using signed cryptographic JSON Web Tokens (PyJWT).
    Validates signature, expiration, issuer, and audience.
    """
    def __init__(
        self,
        secret_key: str = JWT_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        issuer: str = JWT_ISSUER,
        audience: str = JWT_AUDIENCE,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "require": ["exp", "iss", "aud", "sub"],
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "TOKEN_EXPIRED",
                    "message": "Bearer authentication token has expired.",
                },
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\", error_description=\"token expired\""},
            )
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": f"Bearer authentication token is invalid or malformed: {str(e)}",
                },
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )


# Default token verifier singleton
_default_verifier: TokenVerifier = JWTTokenVerifier()


def get_token_verifier() -> TokenVerifier:
    """Returns the active TokenVerifier implementation (replaceable for testing / external IDPs)."""
    return _default_verifier


def set_token_verifier(verifier: TokenVerifier) -> None:
    """Allows runtime replacement of the token verifier."""
    global _default_verifier
    _default_verifier = verifier


def create_token(
    principal_id: uuid.UUID,
    principal_type: str = "user",
    expires_in_minutes: int = JWT_EXPIRY_MINUTES,
    extra_claims: Optional[Dict[str, Any]] = None,
    secret_key: str = JWT_SECRET_KEY,
    algorithm: str = JWT_ALGORITHM,
    issuer: str = JWT_ISSUER,
    audience: str = JWT_AUDIENCE,
) -> str:
    """
    Utility to mint standard signed JWT tokens for testing, API clients, and services.
    """
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(principal_id),
        "principal_type": principal_type,
        "iss": issuer,
        "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
    }
    if principal_type == "brand":
        claims["brand_id"] = str(principal_id)
    else:
        claims["user_id"] = str(principal_id)

    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, secret_key, algorithm=algorithm)


# -----------------------------------------------------------------------------
# Principal Extraction Dependencies
# -----------------------------------------------------------------------------

def get_current_user_id(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_user_id: Optional[str] = Header(None),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> uuid.UUID:
    """
    Extracts authenticated user_id strictly from verified Bearer token claims.
    
    Security Policies:
    - In PRODUCTION:
      1. Missing Bearer credentials strictly return 401 Unauthorized.
      2. Headers like X-User-Id are strictly rejected/ignored (cannot forge identity).
      3. Fallback identities are strictly disabled.
    - In DEVELOPMENT ONLY (if ALLOW_DEV_AUTH is True):
      1. A valid Bearer token takes precedence.
      2. If no Bearer token, allows X-User-Id header or falls back to demo identity.
      3. An invalid Bearer token ALWAYS raises 401 Unauthorized (never falls back on bad credentials).
    """
    # 1. Bearer Token Verification (Highest Precedence)
    if auth_creds and auth_creds.credentials:
        raw_token = auth_creds.credentials.strip()
        # Handle development shorthand raw UUID token ONLY in dev mode
        if ALLOW_DEV_AUTH and not IS_PRODUCTION:
            try:
                return uuid.UUID(raw_token)
            except ValueError:
                pass

        # Verify real JWT
        claims = verifier.verify_token(raw_token)
        principal_type = claims.get("principal_type", "user")
        if principal_type not in ("user", "shopper", "customer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLE",
                    "message": f"Expected user principal, but token has principal_type '{principal_type}'.",
                },
            )
        user_id_str = claims.get("user_id") or claims.get("sub")
        try:
            return uuid.UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_PRINCIPAL", "message": "Token claims contain invalid user UUID."},
            )

    # 2. Production Enforcement: No fallback permitted
    if IS_PRODUCTION or not ALLOW_DEV_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "CREDENTIALS_MISSING",
                "message": "Authentication required. Provide a valid Bearer token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Development-Only Fallback
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_HEADER_UUID", "message": "X-User-Id must be a valid UUID string."},
            )

    return DEFAULT_DEV_USER_ID


def get_current_brand_id(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_brand_id: Optional[str] = Header(None),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> uuid.UUID:
    """
    Extracts authenticated merchant brand_id strictly from verified Bearer token claims.
    
    Security Policies:
    - In PRODUCTION:
      1. Missing Bearer credentials strictly return 401 Unauthorized.
      2. Headers like X-Brand-Id are strictly rejected/ignored (cannot forge identity).
      3. Fallback identities are strictly disabled.
    - In DEVELOPMENT ONLY (if ALLOW_DEV_AUTH is True):
      1. A valid Bearer token takes precedence.
      2. If no Bearer token, allows X-Brand-Id header or falls back to demo brand.
      3. An invalid Bearer token ALWAYS raises 401 Unauthorized (never falls back on bad credentials).
    """
    # 1. Bearer Token Verification
    if auth_creds and auth_creds.credentials:
        raw_token = auth_creds.credentials.strip()
        # Handle development shorthand raw UUID token ONLY in dev mode
        if ALLOW_DEV_AUTH and not IS_PRODUCTION:
            try:
                return uuid.UUID(raw_token)
            except ValueError:
                pass

        # Verify real JWT
        claims = verifier.verify_token(raw_token)
        principal_type = claims.get("principal_type", "brand")
        if principal_type not in ("brand", "merchant", "seller"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLE",
                    "message": f"Expected brand/merchant principal, but token has principal_type '{principal_type}'.",
                },
            )
        brand_id_str = claims.get("brand_id") or claims.get("sub")
        try:
            return uuid.UUID(brand_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_PRINCIPAL", "message": "Token claims contain invalid brand UUID."},
            )

    # 2. Production Enforcement: No fallback permitted
    if IS_PRODUCTION or not ALLOW_DEV_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "CREDENTIALS_MISSING",
                "message": "Merchant authentication required. Provide a valid Bearer token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Development-Only Fallback
    if x_brand_id:
        try:
            return uuid.UUID(x_brand_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_HEADER_UUID", "message": "X-Brand-Id must be a valid UUID string."},
            )

    return DEFAULT_DEV_BRAND_ID
