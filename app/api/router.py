"""Main API router that includes sub-routers."""
from fastapi import APIRouter
from app.api.routes.guardian import router as guardian_router
from app.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(guardian_router, prefix="", tags=["guardian"])

