"""
WearWise Commerce Backend Configuration
Loads settings from root .env or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

for candidate in [ROOT_DIR / ".env", BACKEND_DIR / ".env", Path(".env")]:
    if candidate.is_file():
        load_dotenv(candidate, override=False)
        break

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_COMMERCE_DB = os.getenv("MONGODB_COMMERCE_DB", "wearwise_commerce")
MONGODB_BODY_ENGINE_DB = os.getenv("MONGODB_BODY_ENGINE_DB", "wearwise_body_engine")
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
APP_ENV = os.getenv("APP_ENV", "development")
