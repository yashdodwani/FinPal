"""
Pydantic schema package for the Financial Safety Net project.

This package exposes the most commonly used models so they can be imported as:

    from app.schemas import UserRequest, AgentResponse, RouteEnum, ...

Add new exports to __all__ as the project grows.
"""

from .common import RouteEnum, UserRequest, AgentResponse, AgentError
from .loan import (
    LoanDocumentSource,
    LoanIngestionRequest,
    LoanClause,
    LoanExtractedData,
    LoanRiskData,
    LoanSummaryResponse,
)
from .policy import (
    PolicyRawDocument,
    PolicyEntry,
    PolicyQARequest,
    PolicyQAResponse,
)
from .scam import (
    ScamCategory,
    ScamPattern,
    ScamAnalysisRequest,
    ScamAnalysisResult,
)

__all__ = [
    # common
    "RouteEnum",
    "UserRequest",
    "AgentResponse",
    "AgentError",
    # loan
    "LoanDocumentSource",
    "LoanIngestionRequest",
    "LoanClause",
    "LoanExtractedData",
    "LoanRiskData",
    "LoanSummaryResponse",
    # policy
    "PolicyRawDocument",
    "PolicyEntry",
    "PolicyQARequest",
    "PolicyQAResponse",
    # scam
    "ScamCategory",
    "ScamPattern",
    "ScamAnalysisRequest",
    "ScamAnalysisResult",
]
