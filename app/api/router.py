"""
Main API router.

Includes:
- /health
- /guardian
- /honeypot
"""

from fastapi import APIRouter

from app.api.routes import health, guardian, honeypot

api_router = APIRouter()

# Health check
api_router.include_router(health.router)

# Guardian multi-agent endpoint
api_router.include_router(guardian.router)

# Honeypot endpoint for scammer engagement
api_router.include_router(honeypot.router)
