"""
Shared dependencies for FastAPI routes.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an async SQLAlchemy session.

    NeonDB connection should be configured in app.db.session.async_session_maker.
    """
    async with async_session_maker() as session:
        yield session
