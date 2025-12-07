"""
Pydantic models for the Policy & Rules agent team.

These represent:
- raw regulatory/policy text fetched from RBI/SEBI/etc.
- summarized, user-friendly entries
- incoming QA requests and answers
"""

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class PolicyRawDocument(BaseModel):
    """
    Raw policy/regulation text fetched from the web or static files.
    """

    id: str = Field(..., description="Internal identifier for this policy document.")
    source: Optional[str] = Field(
        default=None, description="Source organization, e.g. 'RBI', 'SEBI', 'NPCI'."
    )
    title: str = Field(..., description="Title or heading of the policy.")
    url: Optional[HttpUrl] = Field(
        default=None, description="Optional URL where this policy can be read."
    )
    raw_text: str = Field(..., description="Full raw text or significant excerpt.")


class PolicyEntry(BaseModel):
    """
    Summarized policy entry stored for RAG and direct lookup.

    This is typically produced by the Policy Summarizer agent.
    """

    id: str = Field(..., description="Internal identifier (can reference PolicyRawDocument.id).")
    title: str = Field(..., description="Short, user-friendly title.")
    category: str = Field(
        ...,
        description="Logical category, e.g. 'upi_fraud', 'digital_lending', 'chargeback_process'.",
    )
    target_user: str = Field(
        default="general_public",
        description="Intended audience, e.g. 'general_public', 'merchants'.",
    )
    summary_bullets: List[str] = Field(
        default_factory=list, description="Key bullet-point takeaways from the policy."
    )
    when_it_applies: Optional[str] = Field(
        default=None,
        description="Short explanation: when does this rule apply?",
    )
    actions_if_affected: List[str] = Field(
        default_factory=list,
        description="Step-by-step actions a user should take if they are impacted.",
    )


class PolicyQARequest(BaseModel):
    """
    Request object from master agent to the Policy QA pipeline.
    """

    question: str = Field(..., description="User's natural-language question.")
    language: str = Field(
        default="en", description="Language in which to answer."
    )
    # Optionally, you could add user profile info, state, etc.


class PolicyQAResponse(BaseModel):
    """
    Answer returned from the Policy QA pipeline.

    'sources' can be used to display which policy entries were used.
    """

    language: str = Field(
        default="en", description="Language used in the generated answer."
    )
    answer: str = Field(
        ..., description="Plain-language answer to the user's policy/regulation question."
    )
    steps: List[str] = Field(
        default_factory=list,
        description="Clear steps the user should follow, if applicable.",
    )
    disclaimers: List[str] = Field(
        default_factory=list,
        description="Disclaimers about accuracy, changes in rules, and official verification.",
    )
    source_ids: List[str] = Field(
        default_factory=list,
        description="IDs of PolicyEntry objects used to answer this question.",
    )
