"""Application configuration loaded from environment variables.

Uses Pydantic BaseSettings to load:
- GEMINI_API_KEY
- DATABASE_URL (NeonDB, asyncpg)
- LOG_LEVEL
"""
from pydantic import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str | None = None
    DATABASE_URL: str | None = None
    LOG_LEVEL: str = "info"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

