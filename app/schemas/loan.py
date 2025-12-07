"""
Pydantic models for the Loan & Insurance agent team.

These schemas correspond to:
- raw document ingestion
- extracted structured data
- risk scoring
- final human-friendly summary
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class LoanDocumentSource(BaseModel):
    """
    Source description for a loan/insurance document.

    For the hackathon you might pass either:
    - text_content directly (for quick testing), or
    - file_id/url and resolve it elsewhere.
    """

    file_id: Optional[str] = Field(
        default=None,
        description="Identifier for an uploaded file (PDF/image) stored by backend.",
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional URL if the document is loaded from a public link.",
    )
    text_content: Optional[str] = Field(
        default=None,
        description="Optional raw text content, used mainly for testing.",
    )


class LoanProductType(str, Enum):
    HOME_LOAN = "home_loan"
    BIKE_LOAN = "bike_loan"
    PERSONAL_LOAN = "personal_loan"
    CAR_LOAN = "car_loan"
    CREDIT_CARD = "credit_card"
    HEALTH_INSURANCE = "health_insurance"
    OTHER = "other"


class LoanIngestionRequest(BaseModel):
    """
    Request from master agent to the Loan pipeline.

    The first stage (ingestion agent) will resolve the actual text from this source.
    """

    language: str = Field(
        default="en", description="User's preferred explanation language."
    )
    source: LoanDocumentSource = Field(
        ..., description="Where to read the loan/insurance document from."
    )


class LoanClause(BaseModel):
    """
    Represents an important clause or section in the document, as understood by the LLM.
    """

    title: str = Field(..., description="Short title created by the model.")
    summary: str = Field(..., description="Plain-language explanation of the clause.")
    risk_level: str = Field(
        default="medium",
        description="Qualitative level: e.g. 'low', 'medium', 'high'.",
    )
    raw_text_snippet: Optional[str] = Field(
        default=None,
        description="Optional raw snippet from the original document.",
    )


class LoanExtractedData(BaseModel):
    """
    Structured representation of key loan/insurance fields.

    NOTE: Use strings for many numeric fields to avoid parsing headaches during the hackathon.
    """

    product_type: LoanProductType = Field(
        default=LoanProductType.OTHER, description="Type of financial product."
    )
    principal_amount: Optional[str] = Field(
        default=None,
        description="Principal amount string, e.g. '₹1,00,000'.",
    )
    interest_rate: Optional[str] = Field(
        default=None,
        description="Interest rate string, e.g. '14% p.a.'.",
    )
    tenure_months: Optional[int] = Field(
        default=None,
        description="Tenure in months, if available.",
    )
    processing_fee: Optional[str] = Field(
        default=None,
        description="Processing fee, e.g. '2%' or '₹1,000'.",
    )
    prepayment_charges: Optional[str] = Field(
        default=None,
        description="Prepayment / foreclosure charges description.",
    )
    late_payment_penalty: Optional[str] = Field(
        default=None, description="Late EMI/payment penalty details."
    )
    other_charges: List[str] = Field(
        default_factory=list,
        description="Other charges or fees mentioned in the document.",
    )
    important_clauses: List[LoanClause] = Field(
        default_factory=list,
        description="List of important clauses extracted by the model.",
    )


class LoanRiskData(BaseModel):
    """
    Result of the risk scoring agent.
    """

    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Numeric risk between 0 (safe) and 1 (very risky)."
    )
    overall_risk_level: str = Field(
        ...,
        description="One of 'low', 'medium', 'high'. You can enforce this via Literal if you prefer.",
    )
    flagged_clauses: List[LoanClause] = Field(
        default_factory=list, description="Subset of clauses that are concerning."
    )
    explanation: Optional[str] = Field(
        default=None, description="Short textual justification of the risk score."
    )


class LoanSummaryResponse(BaseModel):
    """
    Final payload returned by the Loan pipeline to the master agent.

    This is what you can send back to the frontend for the loan explanation view.
    """

    language: str = Field(
        default="en", description="Language used in the generated text."
    )
    extracted: LoanExtractedData = Field(
        ..., description="Structured fields extracted from the document."
    )
    risk: LoanRiskData = Field(
        ..., description="Risk scoring information based on the extracted data."
    )
    plain_summary: str = Field(
        ...,
        description="Short paragraph explaining the loan/insurance in simple language.",
    )
    key_numbers: List[str] = Field(
        default_factory=list,
        description="Bullet points for key numeric facts (principal, tenure, EMI estimate, etc.).",
    )
    risk_explanation: List[str] = Field(
        default_factory=list,
        description="Bullet points explaining why the loan is low/medium/high risk.",
    )
    suggested_questions_for_bank: List[str] = Field(
        default_factory=list,
        description="Questions the user should ask the lender/agent before signing.",
    )
