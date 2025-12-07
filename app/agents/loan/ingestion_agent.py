"""
Ingestion Agent
---------------
Takes: LoanIngestionRequest
Returns: raw text extracted from PDF/image/text

This version is simplified for a hackathon:
- If text_content exists → use it
- If file_id starts with "sample:" → load JSON from app/data/loan_samples
- Else if file_id exists → TODO: fetch from storage / OCR
"""

from pathlib import Path
from typing import Any, Dict

from app.schemas import LoanIngestionRequest

# If you keep using Gemini Vision later, you can import run_gemini again.
# from app.core.gemini import run_gemini


PROMPT_PATH = Path("app/agents/loan/prompts/ingestion_prompt.txt")
SAMPLES_DIR = Path("app/data/loan_samples")


async def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _json_to_text(sample: Dict[str, Any]) -> str:
    """
    Turn a loan_samples JSON object into a human-readable description that
    can be fed into the rest of the pipeline or the LLM.

    Works with the sample structures we created:
      - personal_loan_example.json
      - nbfc_microloan.json
      - credit_line_offer.json
      - payday_loan_highrisk.json
    """
    lines = []

    loan_type = sample.get("loan_type", "Loan")
    lines.append(f"Loan Type: {loan_type}")

    if "principal" in sample:
        lines.append(f"Principal: ₹{sample['principal']}")
    if "credit_limit" in sample:
        lines.append(f"Credit Limit: ₹{sample['credit_limit']}")

    if "interest_rate" in sample:
        lines.append(f"Interest Rate: {sample['interest_rate']}")
    if "processing_fee" in sample:
        lines.append(f"Processing Fee: {sample['processing_fee']}")
    if "late_fee" in sample:
        lines.append(f"Late Fee / Penalty: {sample['late_fee']}")

    if "tenure_months" in sample:
        lines.append(f"Tenure: {sample['tenure_months']} months")
    if "tenure_days" in sample:
        lines.append(f"Tenure: {sample['tenure_days']} days")

    if "security" in sample:
        lines.append(f"Security / Collateral: {sample['security']}")

    # Optional descriptive fields
    for key in ("recovery_terms", "risks"):
        value = sample.get(key)
        if isinstance(value, list):
            lines.append(f"{key.replace('_', ' ').title()}:")
            for item in value:
                lines.append(f"- {item}")
        elif isinstance(value, str):
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    if "illegal_clauses" in sample:
        lines.append("Potentially illegal or high-risk clauses:")
        for c in sample["illegal_clauses"]:
            lines.append(f"- {c}")

    if "disclosures" in sample and isinstance(sample["disclosures"], list):
        lines.append("Disclosures / Notes:")
        for d in sample["disclosures"]:
            lines.append(f"- {d}")

    return "\n".join(lines)


def _load_sample_from_id(file_id: str) -> str:
    """
    Interpret file_id of the form 'sample:<name>' as a shortcut to
    app/data/loan_samples/<name>.json
    """
    prefix = "sample:"
    if not file_id.startswith(prefix):
        return ""

    sample_name = file_id[len(prefix) :].strip()
    if not sample_name:
        return ""

    path = SAMPLES_DIR / f"{sample_name}.json"
    if not path.exists():
        print(f"[loan_ingestion] Sample file not found: {path}")
        return ""

    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    # If the file is a list, take the first object; if it's a dict, use it directly
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        return ""

    return _json_to_text(data)


async def run_ingestion_agent(request: LoanIngestionRequest) -> str:
    """
    Resolve text from:
    - request.source.text_content
    - or sample JSON when file_id starts with "sample:"
    - or file_id (future: PDF/image download + OCR)
    """

    source = request.source

    # 1. Direct text provided → use it
    if source.text_content:
        return source.text_content

    # 2. Synthetic sample via file_id="sample:<name>"
    if source.file_id:
        synthetic = _load_sample_from_id(source.file_id)
        if synthetic:
            return synthetic

        # TODO: in future, treat file_id as storage key, download PDF/image,
        #       run OCR / Gemini Vision to extract text.
        # bytes_data = download_from_s3_or_neon(source.file_id)
        # text = await run_gemini_vision(bytes_data)
        # return text

    # 3. Fallback
    return ""
