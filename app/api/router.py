"""
Main API router.

Includes:
- /health
- /guardian
"""

from fastapi import APIRouter

from app.api.routes import health, guardian

api_router = APIRouter()

# Health check
api_router.include_router(health.router)

# Guardian multi-agent endpoint
api_router.include_router(guardian.router)
