"""
Risk Scoring Agent
------------------
Input: LoanExtractedData
Output: LoanRiskData
"""

from app.schemas import LoanExtractedData, LoanRiskData
from app.core.gemini import run_gemini
from pathlib import Path


PROMPT_PATH = "app/agents/loan/prompts/risk_prompt.txt"


async def load_prompt() -> str:
    return Path(PROMPT_PATH).read_text()


async def run_risk_scorer(extracted: LoanExtractedData, language: str) -> LoanRiskData:
    prompt = await load_prompt()

    payload = {
        "system_instruction": prompt,
        "user": {
            "extracted": extracted.model_dump(),
            "language": language,
        },
    }

    llm_response = await run_gemini(payload)

    try:
        return LoanRiskData.model_validate(llm_response)
    except Exception:
        raise ValueError("Failed to parse LoanRiskData from LLM")
