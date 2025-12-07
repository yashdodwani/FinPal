"""
Narrator Agent
--------------
Turns extracted fields + risk data → user-friendly explanation.

Output: LoanSummaryResponse
"""

from app.schemas import (
    LoanExtractedData,
    LoanRiskData,
    LoanSummaryResponse,
)
from app.core.gemini import run_gemini
from pathlib import Path


PROMPT_PATH = "app/agents/loan/prompts/narration_prompt.txt"


async def load_prompt() -> str:
    return Path(PROMPT_PATH).read_text()


async def run_narrator(
    extracted: LoanExtractedData,
    risk: LoanRiskData,
    language: str,
) -> LoanSummaryResponse:

    prompt = await load_prompt()

    payload = {
        "system_instruction": prompt,
        "user": {
            "extracted": extracted.model_dump(),
            "risk": risk.model_dump(),
            "language": language,
        },
    }

    llm_response = await run_gemini(payload)

    try:
        return LoanSummaryResponse.model_validate(llm_response)
    except Exception:
        raise ValueError("Failed to parse LoanSummaryResponse from LLM")
