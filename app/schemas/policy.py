"""Pydantic models for policy docs and QA."""
from pydantic import BaseModel

class PolicyEntry(BaseModel):
    source: str | None = None
    text: str | None = None

class PolicyQARequest(BaseModel):
    question: str

