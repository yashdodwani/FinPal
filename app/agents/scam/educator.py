import json
from pathlib import Path

from app.schemas.scam import ScamAnalysisResult
from app.core.gemini import run_gemini

EDUCATOR_PROMPT_PATH = Path(__file__).parent / "prompts" / "educator_prompt.txt"
EDUCATOR_PROMPT = EDUCATOR_PROMPT_PATH.read_text(encoding="utf-8")


async def enrich_explanation(result: ScamAnalysisResult) -> ScamAnalysisResult:
    """
    Calls LLM only to improve explanation — does NOT change risk score or classification.
    """
    prompt = EDUCATOR_PROMPT + "\n\nDATA:\n" + json.dumps(result.model_dump())

    payload = {
        "system_instruction": "You are a helpful financial safety educator.",
        "user": {"text": prompt},
    }

    try:
        update = await run_gemini(payload)
    except Exception:
        return result  # fallback on any error

    # If run_gemini gave raw text under 'raw_output', try JSON parse:
    if isinstance(update, dict) and "raw_output" in update:
        try:
            update = json.loads(update["raw_output"])
        except json.JSONDecodeError:
            return result

    if not isinstance(update, dict):
        return result

    result.short_warning = update.get("short_warning", result.short_warning)
    result.detailed_explanation = update.get(
        "detailed_explanation", result.detailed_explanation
    )
    result.recommended_action = update.get("what_to_do_now", result.recommended_action)

    return result
