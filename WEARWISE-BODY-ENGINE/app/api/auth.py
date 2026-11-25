"""
WearWise API Authentication & Ownership Dependencies
Implements replaceable TokenVerifier protocol and JWT signature/issuer/audience/expiry validation.
Strictly distinguishes production mode from development-only identity adapters.
Declares standard Bearer security scheme in OpenAPI.
Never trusts client-supplied user or brand IDs from request bodies.
"""

import hmac
import time
import uuid
from typing import Optional, Dict, Any, Protocol
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import Cookie, Header, HTTPException, Request, status, Depends
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
from app.db import mongo

AUTH_COOKIE_NAME = "ww_auth_session"
CSRF_COOKIE_NAME = "ww_csrf_token"
UNSAFE_HTTP_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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

def _validate_session_claims(claims: Dict[str, Any]) -> None:
    """Checks server-side session revocation and Commerce user active/approval state when linked."""
    jti = claims.get("jti")
    if jti:
        sess_col = mongo.get_commerce_collection("auth_sessions")
        if sess_col is not None:
            sess = sess_col.find_one({"jti": jti}, {"_id": 0, "revoked": 1})
            if sess and sess.get("revoked"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "SESSION_REVOKED", "message": "Session has been signed out."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
    commerce_uid = claims.get("commerce_user_id")
    if commerce_uid:
        users_col = mongo.get_commerce_collection("users")
        if users_col is not None:
            user_doc = users_col.find_one({"id": commerce_uid}, {"_id": 0, "status": 1, "is_active": 1, "role": 1, "seller_approved": 1})
            if user_doc is not None:
                if not user_doc.get("is_active", True) or user_doc.get("status") == "suspended":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"code": "ACCOUNT_INACTIVE", "message": "Account is inactive or suspended."},
                    )
                if user_doc.get("role") == "seller" and (not user_doc.get("seller_approved", False) or user_doc.get("status") != "active"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={"code": "SELLER_NOT_APPROVED", "message": "Seller account is not approved or active."},
                    )


def _extract_bearer_or_cookie_token(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials],
    session_cookie: Optional[str],
) -> tuple[Optional[str], bool]:
    if auth_creds and auth_creds.credentials:
        return auth_creds.credentials.strip(), False
    if session_cookie:
        if request.method.upper() in UNSAFE_HTTP_METHODS:
            csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
            csrf_header = request.headers.get("x-csrf-token")
            if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "CSRF_FAILED", "message": "CSRF token validation failed."},
                )
        return session_cookie.strip(), True
    return None, False


def _coerce_uuid(raw_id: Any) -> uuid.UUID:
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"wearwise:{raw_id}")


def get_current_user_id(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session_cookie: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    x_user_id: Optional[str] = Header(None),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> uuid.UUID:
    """
    Extracts authenticated shopper/user UUID strictly from verified Bearer JWT or HTTP-only session cookie.
    """
    raw_token, used_cookie = _extract_bearer_or_cookie_token(request, auth_creds, session_cookie)
    if raw_token:
        # Handle development shorthand raw UUID token ONLY in dev mode (header only)
        if not used_cookie and ALLOW_DEV_AUTH and not IS_PRODUCTION:
            try:
                return uuid.UUID(raw_token)
            except ValueError:
                pass

        # Verify real JWT
        claims = verifier.verify_token(raw_token)
        _validate_session_claims(claims)
        principal_type = str(claims.get("principal_type") or claims.get("role") or "user").lower()
        if principal_type not in ("user", "shopper", "customer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLE",
                    "message": f"Expected shopper/user principal, but token has principal_type '{principal_type}'.",
                },
            )
        user_id_str = claims.get("user_id") or claims.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_PRINCIPAL", "message": "Token claims missing user identifier."},
            )
        return _coerce_uuid(user_id_str)

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

    # 3. Development-Only Fallback (for unauthenticated shopper prototype flows)
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
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session_cookie: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    x_brand_id: Optional[str] = Header(None),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> uuid.UUID:
    """
    Extracts authenticated seller/brand UUID strictly from verified Bearer JWT or HTTP-only session cookie.
    Never falls back silently to an unauthenticated default brand — requires credentials or explicit dev X-Brand-Id.
    """
    raw_token, used_cookie = _extract_bearer_or_cookie_token(request, auth_creds, session_cookie)
    if raw_token:
        # Handle development shorthand raw UUID token ONLY in dev mode (header only)
        if not used_cookie and ALLOW_DEV_AUTH and not IS_PRODUCTION:
            try:
                return uuid.UUID(raw_token)
            except ValueError:
                pass

        # Verify real JWT
        claims = verifier.verify_token(raw_token)
        _validate_session_claims(claims)
        principal_type = str(claims.get("principal_type") or claims.get("role") or "").lower()
        if principal_type not in ("brand", "merchant", "seller"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_ROLE",
                    "message": f"Expected seller/merchant principal, but token has role '{principal_type or 'shopper'}'.",
                },
            )
        brand_id_str = claims.get("brand_id") or claims.get("sub")
        try:
            return uuid.UUID(str(brand_id_str))
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_PRINCIPAL", "message": "Token claims contain invalid brand UUID."},
            )

    # Development-Only explicit header for isolated integration tests
    if ALLOW_DEV_AUTH and not IS_PRODUCTION and x_brand_id:
        try:
            return uuid.UUID(x_brand_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_HEADER_UUID", "message": "X-Brand-Id must be a valid UUID string."},
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "CREDENTIALS_MISSING",
            "message": "Seller authentication required. Please sign in through Seller Portal.",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
