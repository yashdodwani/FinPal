"""
Common Pydantic models shared across agents.

These keep the contract between:
- FastAPI routes
- Master router agent
- Individual sub-agent pipelines (loan, policy, scam)
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RouteEnum(str, Enum):
    """High-level intent / route for the master agent."""

    SCAM_CHECK = "SCAM_CHECK"
    LOAN_DOC = "LOAN_DOC"
    POLICY_QA = "POLICY_QA"


class AgentError(BaseModel):
    """Represents an error produced by an agent."""

    message: str = Field(..., description="Human-readable error message.")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional structured details for debugging."
    )


class UserRequest(BaseModel):
    """
    Generic request envelope received by the /guardian endpoint.

    The master agent will look at:
    - route (optional hint)
    - text (user's message)
    - language
    - optional doc/file metadata
    and then decide which sub-agent graph to call.
    """

    route_hint: Optional[RouteEnum] = Field(
        default=None,
        description=(
            "Optional client-provided route hint. "
            "If None, the master agent will infer the route."
        ),
    )
    text: Optional[str] = Field(
        default=None,
        description="Optional free-form text (SMS, WhatsApp message, question, etc.).",
    )
    language: str = Field(
        default="en",
        description="BCP-47 language code, e.g. 'en', 'en-IN', 'hi'.",
    )
    file_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional file identifier if the user uploaded a document via another API "
            "(e.g. loan PDF, image). The backend will resolve this to content."
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional arbitrary metadata (e.g. UPI ID, URL, channel).",
    )


class AgentResponse(BaseModel):
    """
    Generic wrapper around sub-agent outputs.

    `data` is intentionally untyped (Any) so each pipeline can return its own model.
    The FastAPI endpoint can either:
    - keep this generic, or
    - unwrap to more specific models depending on `final_route`.
    """

    final_route: RouteEnum = Field(
        ..., description="Route that was actually executed by the master agent."
    )
    data: Any = Field(
        ..., description="Pipeline-specific payload (loan/scam/policy model)."
    )
    error: Optional[AgentError] = Field(
        default=None,
        description="Filled when an error occurs in any stage of the pipeline.",
    )
    debug_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional debug info (e.g. intermediate routes, prompts). "
            "Remove or sanitize in production."
        ),
    )
