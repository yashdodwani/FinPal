"""
Pydantic models for the Scam Protection agent team.

These schemas cover:
- stored scam patterns (from news, manual examples)
- incoming analysis requests (user messages)
- analysis results (risk assessment + explanation)
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ScamCategory(str, Enum):
    """High-level categories of scams."""

    UPI_REFUND = "upi_refund"
    PHISHING_LINK = "phishing_link"
    OTP_PHISHING = "otp_phishing"
    KYC_VERIFICATION = "kyc_verification"
    INVESTMENT = "investment"
    LOTTERY = "lottery"
    OTHER = "other"


class ScamPattern(BaseModel):
    """
    Generalized scam pattern extracted from news or manual labeling.

    Stored in JSON / DB and used for similarity search & explanations.
    """

    id: str = Field(..., description="Unique ID for this pattern.")
    scam_name: str = Field(..., description="Short name, e.g. 'Fake UPI refund request'.")
    category: ScamCategory = Field(
        default=ScamCategory.OTHER, description="High-level category of scam."
    )
    channel: str = Field(
        ...,
        description="Channel used, e.g. 'UPI', 'SMS', 'WhatsApp', 'Call', 'Website', 'App'.",
    )
    modus_operandi: str = Field(
        ..., description="Description of how this scam works in general."
    )
    key_phrases: List[str] = Field(
        default_factory=list,
        description="Typical phrases or patterns that appear in messages for this scam.",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Important warning signs for this scam pattern.",
    )
    recommended_user_action: str = Field(
        ..., description="What the user should do when confronted with this scam."
    )
    example_message: Optional[str] = Field(
        default=None,
        description="Example SMS/WhatsApp text or script used in the scam.",
    )
    source_url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional link to a news article or reference.",
    )


class ScamAnalysisRequest(BaseModel):
    """
    Request from master agent to the Scam analysis pipeline.

    'text' is mandatory (SMS/WhatsApp/email/etc.).
    Optional metadata can include URLs, UPI IDs, etc.
    """

    text: str = Field(
        ..., description="User-provided suspicious message or description."
    )
    language: str = Field(
        default="en", description="Language in which explanations should be returned."
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional URL extracted from the message.",
    )
    upi_id: Optional[str] = Field(
        default=None,
        description="Optional UPI ID or handle mentioned.",
    )
    channel: Optional[str] = Field(
        default=None,
        description="Optional channel hint: 'SMS', 'WhatsApp', 'UPI', etc.",
    )


class ScamAnalysisResult(BaseModel):
    """
    Output of the Scam Risk Analyzer + Educator pipeline.

    This can be wrapped inside AgentResponse.data.
    """

    language: str = Field(
        default="en", description="Language used in the generated explanation."
    )
    classification: str = Field(
        ...,
        description="LLM-generated label, e.g. 'likely scam', 'probably safe', 'uncertain'.",
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numeric risk score from 0 (safe) to 1 (very risky).",
    )
    is_scam: bool = Field(
        ...,
        description="Model's best guess whether this is a scam.",
    )
    matched_patterns: List[str] = Field(
        default_factory=list,
        description="IDs or names of ScamPattern objects that closely match this message.",
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Bullet points explaining what looks suspicious.",
    )
    recommended_action: str = Field(
        ..., description="What the user should do next (e.g. ignore, block, report)."
    )
    short_warning: str = Field(
        ...,
        description="One or two lines for quick UI display (banner/toast).",
    )
    detailed_explanation: List[str] = Field(
        default_factory=list,
        description="More detailed bullet points educating the user about this scam type.",
    )


class ScamArticle(BaseModel):
    """
    A raw news article fetched from the web.
    """
    headline: Optional[str] = None
    raw_text: str
    published: str
    url: Optional[str] = None


class HarvestResponse(BaseModel):
    """
    Response from the scam harvesting endpoint.
    """
    articles_found: int
    patterns_extracted: int
    patterns: List[ScamPattern]
    articles: List[ScamArticle]
