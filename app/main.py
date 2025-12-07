"""FastAPI application entrypoint and factory.

Provides a minimal app with root endpoint and router inclusion.
"""
from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="FinPal API")

@app.get("/")
async def root():
    return {"message": "Financial Safety Net API"}

# Include API routers
app.include_router(api_router)

