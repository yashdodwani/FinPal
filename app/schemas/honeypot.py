"""
Pydantic models for the Agentic Honeypot System.

These schemas cover:
- Session state management
- Engagement stages
- Intelligence extraction
- Callback payloads
- Honeypot-specific requests/responses
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class EngagementStage(str, Enum):
    """Engagement lifecycle stages."""
    INIT = "INIT"
    TRUST_BUILDING = "TRUST_BUILDING"
    DATA_EXTRACTION = "DATA_EXTRACTION"
    EXIT = "EXIT"


class ExtractedIntelligence(BaseModel):
    """Structured intelligence extracted from scammer messages."""
    
    bank_accounts: List[str] = Field(
        default_factory=list,
        description="Bank account numbers extracted from conversation."
    )
    upi_ids: List[str] = Field(
        default_factory=list,
        description="UPI IDs (e.g., name@upi, phone@bank) extracted."
    )
    phishing_urls: List[str] = Field(
        default_factory=list,
        description="Suspicious URLs/links shared by scammer."
    )
    phone_numbers: List[str] = Field(
        default_factory=list,
        description="Phone numbers mentioned by scammer."
    )
    scam_keywords: List[str] = Field(
        default_factory=list,
        description="Key scam indicators and phrases detected."
    )
    email_addresses: List[str] = Field(
        default_factory=list,
        description="Email addresses mentioned."
    )
    app_names: List[str] = Field(
        default_factory=list,
        description="Apps scammer asked victim to install."
    )
    payment_requests: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Payment requests with amounts if mentioned."
    )


class ConversationMessage(BaseModel):
    """Single message in honeypot conversation."""
    
    role: str = Field(..., description="'scammer' or 'honeypot'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extracted_this_turn: Optional[ExtractedIntelligence] = Field(
        default=None,
        description="Intelligence extracted from this specific message."
    )


class HoneypotSessionState(BaseModel):
    """
    Persistent state for a honeypot engagement session.
    Stored in memory or database per sessionId.
    """
    
    session_id: str = Field(..., description="Unique session identifier.")
    stage: EngagementStage = Field(
        default=EngagementStage.INIT,
        description="Current engagement stage."
    )
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="Full conversation history."
    )
    accumulated_intelligence: ExtractedIntelligence = Field(
        default_factory=ExtractedIntelligence,
        description="All intelligence accumulated across turns."
    )
    scam_type_detected: Optional[str] = Field(
        default=None,
        description="Type of scam detected (if identified)."
    )
    scam_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence that this is a scam."
    )
    persona_name: str = Field(
        default="Priya",
        description="Name of the honeypot persona."
    )
    persona_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Persona background details for consistency."
    )
    information_requested_by_scammer: List[str] = Field(
        default_factory=list,
        description="What info the scammer has asked for."
    )
    information_seemingly_shared: List[str] = Field(
        default_factory=list,
        description="What info honeypot pretended to share."
    )
    turns_without_progress: int = Field(
        default=0,
        description="Counter for stagnant turns."
    )
    max_turns: int = Field(
        default=20,
        description="Maximum turns before forced exit."
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    callback_sent: bool = Field(
        default=False,
        description="Whether final callback has been sent."
    )


class HoneypotRequest(BaseModel):
    """
    Incoming request to the honeypot endpoint.
    Each message from the scammer comes through this.
    """
    
    session_id: str = Field(..., description="Session identifier for multi-turn tracking.")
    text: str = Field(..., description="Scammer's message.")
    language: str = Field(default="en", description="Language code.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (channel, timestamp, etc.)."
    )


class HoneypotResponse(BaseModel):
    """
    Response from honeypot agent.
    Appears as a normal human reply - NO metadata leakage.
    """
    
    status: str = Field(default="success", description="Always 'success' during engagement.")
    reply: str = Field(..., description="Human-like message to send back.")


class HoneypotCallbackPayload(BaseModel):
    """
    Final callback payload sent to evaluation endpoint.
    Sent exactly once when engagement completes.
    """
    
    sessionId: str = Field(..., description="Session identifier.")
    scamDetected: bool = Field(default=True, description="Always true for honeypot callbacks.")
    totalMessagesExchanged: int = Field(..., description="Total messages in conversation.")
    extractedIntelligence: ExtractedIntelligence = Field(
        ..., description="All extracted intelligence."
    )
    agentNotes: str = Field(
        ..., description="Brief behavioral summary of the engagement."
    )
    scamType: Optional[str] = Field(
        default=None,
        description="Classified scam type if identified."
    )
    engagementDuration: Optional[int] = Field(
        default=None,
        description="Duration in seconds from first to last message."
    )
    confidenceScore: float = Field(
        default=0.0,
        description="Final confidence that this was a scam."
    )


class EngagementStrategy(str, Enum):
    """Tactical options for the honeypot agent."""
    
    ASK_CLARIFICATION = "ask_clarification"
    PRETEND_CONFUSION = "pretend_confusion"
    DELAY_COMPLIANCE = "delay_compliance"
    REQUEST_VERIFICATION = "request_verification"
    CLAIM_PARTIAL_COMPLIANCE = "claim_partial_compliance"
    EXPRESS_WORRY = "express_worry"
    TECHNICAL_DIFFICULTY = "technical_difficulty"


class InternalHoneypotState(BaseModel):
    """
    Internal state passed between honeypot sub-agents.
    Never exposed in responses.
    """
    
    session: HoneypotSessionState
    current_scammer_message: str
    detected_intent: Optional[str] = None
    recommended_strategy: Optional[EngagementStrategy] = None
    new_extractions: Optional[ExtractedIntelligence] = None
    should_exit: bool = False
    exit_reason: Optional[str] = None
