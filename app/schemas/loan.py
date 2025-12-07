"""Pydantic models for loan extraction and risk."""
from pydantic import BaseModel

class LoanDocument(BaseModel):
    content: str | None = None

class LoanRiskResult(BaseModel):
    score: float | None = None
    details: dict | None = None

