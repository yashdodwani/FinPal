"""Pydantic models for scam patterns and analysis."""
from pydantic import BaseModel

class ScamPatternModel(BaseModel):
    name: str | None = None
    description: str | None = None

class ScamAnalysis(BaseModel):
    risk_level: str | None = None
    notes: str | None = None

