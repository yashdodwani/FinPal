"""Shared API dependencies (DB session, etc.)."""
from typing import AsyncGenerator
from app.db.session import async_session_maker

async def get_db() -> AsyncGenerator:
    """Yield an async DB session."""
    async with async_session_maker() as session:
        yield session

