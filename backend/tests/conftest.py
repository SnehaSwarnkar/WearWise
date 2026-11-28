"""Pytest startup configuration ensuring staging DB isolation for all backend tests."""

import os

os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
