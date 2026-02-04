"""SQLAlchemy models for FinPal.

Includes:
- ScamPattern: Known scam patterns
- PolicyDoc: Policy documents
- HoneypotSession: Honeypot conversation sessions
- ExtractedIntel: Intelligence extracted from scammers
"""
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON

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


class HoneypotSession(Base):
    """
    Persistent storage for honeypot sessions.
    Tracks full conversation state for multi-turn engagement.
    """
    __tablename__ = "honeypot_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    
    # Engagement state
    stage: Mapped[str] = mapped_column(String(32), default="INIT")
    scam_type: Mapped[str] = mapped_column(String(128), nullable=True)
    scam_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Persona
    persona_name: Mapped[str] = mapped_column(String(64), default="Priya")
    persona_context: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Conversation tracking
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    turns_without_progress: Mapped[int] = mapped_column(Integer, default=0)
    
    # Information tracking
    info_requested: Mapped[list] = mapped_column(JSON, default=list)
    info_shared: Mapped[list] = mapped_column(JSON, default=list)
    
    # Callback status
    callback_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    callback_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("HoneypotMessage", back_populates="session", cascade="all, delete-orphan")
    intelligence = relationship("ExtractedIntel", back_populates="session", uselist=False, cascade="all, delete-orphan")


class HoneypotMessage(Base):
    """Individual messages in a honeypot conversation."""
    __tablename__ = "honeypot_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("honeypot_sessions.session_id"))
    
    role: Mapped[str] = mapped_column(String(16))  # 'scammer' or 'honeypot'
    content: Mapped[str] = mapped_column(Text)
    
    # Per-message extraction
    extracted_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    session = relationship("HoneypotSession", back_populates="messages")


class ExtractedIntel(Base):
    """
    Accumulated intelligence extracted from a honeypot session.
    One record per session, updated incrementally.
    """
    __tablename__ = "extracted_intel"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("honeypot_sessions.session_id"), unique=True)
    
    # Extracted data
    bank_accounts: Mapped[list] = mapped_column(JSON, default=list)
    upi_ids: Mapped[list] = mapped_column(JSON, default=list)
    phishing_urls: Mapped[list] = mapped_column(JSON, default=list)
    phone_numbers: Mapped[list] = mapped_column(JSON, default=list)
    email_addresses: Mapped[list] = mapped_column(JSON, default=list)
    scam_keywords: Mapped[list] = mapped_column(JSON, default=list)
    app_names: Mapped[list] = mapped_column(JSON, default=list)
    payment_requests: Mapped[list] = mapped_column(JSON, default=list)
    
    # Metadata
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    session = relationship("HoneypotSession", back_populates="intelligence")

