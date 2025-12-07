import json
import google.generativeai as genai
import os
from pathlib import Path
from app.schemas.scam import ScamAnalysisResult

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EDUCATOR_PROMPT_PATH = Path(__file__).parent / "prompts" / "educator_prompt.txt"
with open(EDUCATOR_PROMPT_PATH) as f:
    EDUCATOR_PROMPT = f.read()


def enrich_explanation(result: ScamAnalysisResult) -> ScamAnalysisResult:
    """
    Calls LLM only to improve explanation — does NOT change risk score or classification.
    """
    model = genai.GenerativeModel("gemini-2.0-pro")
    prompt = EDUCATOR_PROMPT + "\n\nDATA:\n" + json.dumps(result.model_dump())
    llm_out = model.generate_content(prompt).text

    try:
        update = json.loads(llm_out)
    except:
        return result  # fallback

    result.short_warning = update.get("short_warning", result.short_warning)
    result.detailed_explanation = update.get("detailed_explanation", result.detailed_explanation)
    result.recommended_action = update.get("what_to_do_now", result.recommended_action)

    return result
