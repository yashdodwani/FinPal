"""
Loan & Insurance Pipeline
-------------------------
This glues together:
1. Ingestion
2. Clause extraction
3. Risk scoring
4. Narration
"""

from app.schemas import (
    LoanIngestionRequest,
    LoanSummaryResponse,
    LoanExtractedData,
    LoanRiskData,
)

from .ingestion_agent import run_ingestion_agent
from .clause_extractor import run_clause_extractor
from .risk_scorer import run_risk_scorer
from .narrator import run_narrator


async def run_loan_pipeline(request: LoanIngestionRequest) -> LoanSummaryResponse:
    """
    End-to-end pipeline for loan/insurance understanding.
    """

    # 1. INGESTION → raw text
    raw_text = await run_ingestion_agent(request)

    # 2. CLAUSE EXTRACTION
    extracted: LoanExtractedData = await run_clause_extractor(
        raw_text=raw_text, language=request.language
    )

    # 3. RISK SCORING
    risk: LoanRiskData = await run_risk_scorer(
        extracted=extracted, language=request.language
    )

    # 4. NARRATION → final output
    summary: LoanSummaryResponse = await run_narrator(
        extracted=extracted,
        risk=risk,
        language=request.language,
    )

    return summary
