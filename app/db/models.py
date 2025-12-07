"""Placeholder SQLAlchemy models for FinPal.

Define minimal stubs for future development.
"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

class ScamPattern(Base):
    __tablename__ = "scam_patterns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

class PolicyDoc(Base):
    __tablename__ = "policy_docs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)

