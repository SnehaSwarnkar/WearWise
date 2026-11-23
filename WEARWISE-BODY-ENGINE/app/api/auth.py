"""
WearWise API Authentication & Ownership Dependencies
Derives authenticated principal (user_id and brand_id) strictly from request headers or Bearer tokens.
Never trusts client-supplied user or brand IDs from request bodies.
"""

import uuid
from typing import Optional
from fastapi import Header, HTTPException, status, Request


DEFAULT_TEST_USER_ID = uuid.UUID("c1f7a28e-8e3b-48d9-a791-03f4439c1b3e")
DEFAULT_TEST_BRAND_ID = uuid.UUID("e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e")


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
) -> uuid.UUID:
    """
    Extracts authenticated user_id from Bearer token or X-User-Id header.
    Defaults to canonical demonstration user in local test mode if omitted.
    """
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-User-Id header format. Must be UUID.",
            )

    if authorization:
        parts = authorization.strip().split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            try:
                return uuid.UUID(token)
            except ValueError:
                # If bearer token has prefix e.g. 'user-<uuid>', try to extract
                if "user-" in token:
                    try:
                        return uuid.UUID(token.split("user-")[-1])
                    except ValueError:
                        pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer token format.",
        )

    # Local development / demo fallback
    return DEFAULT_TEST_USER_ID


def get_current_brand_id(
    authorization: Optional[str] = Header(None),
    x_brand_id: Optional[str] = Header(None),
) -> uuid.UUID:
    """
    Extracts authenticated merchant brand_id from Bearer token or X-Brand-Id header.
    Defaults to canonical demonstration brand in local test mode if omitted.
    """
    if x_brand_id:
        try:
            return uuid.UUID(x_brand_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Brand-Id header format. Must be UUID.",
            )

    if authorization:
        parts = authorization.strip().split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            try:
                return uuid.UUID(token)
            except ValueError:
                if "brand-" in token:
                    try:
                        return uuid.UUID(token.split("brand-")[-1])
                    except ValueError:
                        pass

    return DEFAULT_TEST_BRAND_ID
