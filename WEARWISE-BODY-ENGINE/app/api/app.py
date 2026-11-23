"""
WearWise FastAPI Application Main Entrypoint
Initializes FastAPI, registers OpenAPI metadata, standard error handlers, CORS, and versioned routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.api.v1 import v1_router
from app.services.errors import ServiceError
from app.api.errors import service_error_handler, validation_error_handler
from app.db.session import init_db


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

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Canonical Error Envelope Handlers
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # 3. Healthcheck Endpoint
    @app.get("/health", tags=["System"])
    @app.get("/api/v1/health", tags=["System"])
    def health_check():
        return {
            "status": "healthy",
            "phase": "6A",
            "service": "WearWise Backend API",
            "storage_mode": "content_addressable_local",
        }

    # 4. Include Versioned v1 Router
    app.include_router(v1_router)

    return app


app = create_app()
