"""Async SQLAlchemy session and engine configuration.

Uses `DATABASE_URL` from settings. Intended for NeonDB (PostgreSQL) via asyncpg.
TODO: Add connection pooling and SSL settings appropriate for Neon.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL or "postgresql+asyncpg://localhost/test"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

