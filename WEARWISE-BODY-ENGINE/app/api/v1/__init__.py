"""
WearWise API Version 1 Routers
"""

from fastapi import APIRouter

from app.api.v1.profiles import router as profiles_router
from app.api.v1.avatar import router as avatar_router
from app.api.v1.garments import router as garments_router
from app.api.v1.fit import router as fit_router
from app.api.v1.vton import router as vton_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(profiles_router)
v1_router.include_router(avatar_router)
v1_router.include_router(garments_router)
v1_router.include_router(fit_router)
v1_router.include_router(vton_router)

__all__ = ["v1_router"]
