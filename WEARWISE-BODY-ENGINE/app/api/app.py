"""
WearWise FastAPI Application Main Entrypoint
Initializes FastAPI, registers OpenAPI metadata, standard error handlers, CORS, and versioned routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.config import CORS_ALLOWED_ORIGINS, IS_PRODUCTION
from app.api.v1 import v1_router
from app.services.errors import ServiceError
from app.api.errors import (
    service_error_handler,
    validation_error_handler,
    http_exception_handler,
)
from app.db.session import init_db
from app.db import mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Application factory for WearWise backend."""
    app = FastAPI(
        title="WearWise Backend API",
        version="1.0.0",
        description="WearWise AI Fashion & Honest Fit Platform API — Phase 6A Vertical Slice",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Environment-Configured CORS Middleware (No wildcard in production)
    origins = CORS_ALLOWED_ORIGINS if CORS_ALLOWED_ORIGINS else (["*"] if not IS_PRODUCTION else [])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Canonical Error Envelope Handlers
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # 3. Custom OpenAPI schema to include Bearer security scheme definition
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your signed JWT Bearer token (sub=UUID, principal_type='user'|'brand').",
            }
        }
        # Apply BearerAuth security globally to secure routes
        openapi_schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # 4. Healthcheck Endpoint
    @app.get("/health", tags=["System"])
    @app.get("/api/v1/health", tags=["System"])
    def health_check():
        mongo_status = mongo.ping()
        is_healthy = mongo_status.get("ok", False) or not mongo.MONGODB_URI
        return {
            "status": "healthy" if is_healthy else "degraded",
            "phase": "6A",
            "service": "WearWise Backend API",
            "storage_mode": "content_addressable_local",
            "mongodb": mongo_status,
        }

    # 5. Include Versioned v1 Router
    app.include_router(v1_router)

    return app


app = create_app()
