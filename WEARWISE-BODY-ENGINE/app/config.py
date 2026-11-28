"""
WearWise Application Configuration & Environment Settings
Centralizes runtime configuration, security policies, token parameters, and CORS settings.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base directories
REPO_ROOT = Path(__file__).resolve().parent.parent
MONOREPO_ROOT = REPO_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load root .env or local .env
for candidate in [MONOREPO_ROOT / ".env", REPO_ROOT / ".env", Path(".env")]:
    if candidate.is_file():
        load_dotenv(candidate, override=False)
        break

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_BODY_ENGINE_DB = os.getenv("MONGODB_BODY_ENGINE_DB", "wearwise_body_engine")
MONGODB_COMMERCE_DB = os.getenv("MONGODB_COMMERCE_DB", "wearwise_commerce")
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))

# Environment mode: 'development', 'test', 'production'
WEARWISE_ENV = os.getenv("WEARWISE_ENV", os.getenv("ENVIRONMENT", "development")).lower()
IS_PRODUCTION = WEARWISE_ENV == "production"

# In production, dev authentication fallbacks are strictly prohibited
ALLOW_DEV_AUTH = (not IS_PRODUCTION) and (
    os.getenv("ALLOW_DEV_AUTH", "true").lower() in ("true", "1", "yes")
)

# JWT / Token Verification Configuration Contract
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "wearwise-dev-signing-key-for-local-testing-only-32bytes")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "wearwise:auth")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "wearwise:api")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

# Database Configuration
DEFAULT_DB_PATH = DATA_DIR / "wearwise.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# CORS Origins
_default_dev_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

_env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _env_origins:
    CORS_ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _env_origins.split(",") if origin.strip()]
elif not IS_PRODUCTION:
    CORS_ALLOWED_ORIGINS = _default_dev_origins
else:
    CORS_ALLOWED_ORIGINS = []  # In production, must be explicitly configured via CORS_ALLOWED_ORIGINS
