"""
FastAPI application entrypoint for the Financial Safety Net backend.

This app:
- Exposes /health for liveness checks
- Exposes /guardian to talk to the master agent
- Serves frontend static files at root

You can run it with:
    uvicorn app.main:app --reload

For ADK:
- You can also wrap the same agents in an ADK Runner and use `adk web`
  to inspect and debug the workflows visually.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial Safety Net API",
        version="0.1.0",
        description=(
            "Backend for a multi-agent financial safety assistant "
            "that protects users from UPI scams and complex loan policies."
        ),
    )

    # Mount API router (must come before static files)
    app.include_router(api_router)

    # Serve frontend static files at root
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

    return app


app = create_app()
