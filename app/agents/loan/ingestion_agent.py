"""
Ingestion Agent
---------------
Takes: LoanIngestionRequest
Returns: raw text extracted from PDF/image/text

This version is simplified for a hackathon:
- If text_content exists → use it
- If file_id exists → TODO: fetch from storage
"""

from app.schemas import LoanIngestionRequest
from app.core.gemini import run_gemini
from pathlib import Path


PROMPT_PATH = "app/agents/loan/prompts/ingestion_prompt.txt"


async def load_prompt() -> str:
    return Path(PROMPT_PATH).read_text()


async def run_ingestion_agent(request: LoanIngestionRequest) -> str:
    """
    Resolve text from:
    - request.source.text_content
    - or file_id (optional future extension)
    """

    # 1. Direct text provided → use it
    if request.source.text_content:
        return request.source.text_content

    # 2. This is where you'd load a PDF/image for multimodal ingestion
    if request.source.file_id:
        # TODO: download file, convert to bytes, pass to Gemini Vision
        pass

    # Fallback
    return ""
