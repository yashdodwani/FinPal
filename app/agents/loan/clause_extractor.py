"""
Clause Extraction Agent
-----------------------
Input: raw_text
Output: LoanExtractedData (structured model)
"""

from app.schemas import LoanExtractedData
from app.core.gemini import run_gemini
from pathlib import Path
import json

PROMPT_PATH = "app/agents/loan/prompts/clause_prompt.txt"


async def load_prompt() -> str:
    return Path(PROMPT_PATH).read_text()


async def run_clause_extractor(raw_text: str, language: str) -> LoanExtractedData:
    prompt = await load_prompt()

    payload = {
        "system_instruction": prompt,
        "user": {
            "raw_text": raw_text,
            "language": language,
        },
    }

    llm_response = await run_gemini(payload)

    try:
        return LoanExtractedData.model_validate(llm_response)
    except Exception:
        raise ValueError("Failed to parse LoanExtractedData from LLM")
