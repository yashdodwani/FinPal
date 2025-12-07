"""
Loan & Insurance Pipeline
-------------------------

This file glues together:

1. ingestion_agent → extracts raw text
2. clause_extractor → extracts structured fields
3. risk_scorer → computes risk
4. narrator → produces final summary

The master agent calls:  await run_loan_pipeline(LoanIngestionRequest)
"""

from app.schemas import (
    LoanIngestionRequest,
    LoanSummaryResponse,
    LoanExtractedData,
    LoanRiskData,
)

# Import the individual agent stubs
from .ingestion_agent import run_ingestion_agent
from .clause_extractor import run_clause_extractor
from .risk_scorer import run_risk_scorer
from .narrator import run_narrator


async def run_loan_pipeline(request: LoanIngestionRequest) -> LoanSummaryResponse:
    """
    End-to-end pipeline to process a loan or insurance document.
    """

    # 1. Ingestion → get raw text
    raw_text = await run_ingestion_agent(request)

    # 2. Extract structured fields
    extracted: LoanExtractedData = await run_clause_extractor(raw_text, request.language)

    # 3. Risk scoring
    risk: LoanRiskData = await run_risk_scorer(extracted, request.language)

    # 4. Generate plain-language summary
    summary: LoanSummaryResponse = await run_narrator(
        extracted=extracted,
        risk=risk,
        language=request.language,
    )

    return summary
