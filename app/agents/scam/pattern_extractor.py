import json
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.schemas.scam import ScamPattern, ScamCategory
from app.core.gemini import run_gemini

PATTERN_PROMPT_PATH = Path(__file__).parent / "prompts" / "pattern_prompt.txt"
PATTERN_PROMPT = PATTERN_PROMPT_PATH.read_text(encoding="utf-8")


def _guess_category(name: str) -> ScamCategory:
    name = name.lower()
    if "refund" in name:
        return ScamCategory.UPI_REFUND
    if "kyc" in name:
        return ScamCategory.KYC_VERIFICATION
    if "otp" in name:
        return ScamCategory.OTP_PHISHING
    if "investment" in name:
        return ScamCategory.INVESTMENT
    if "lottery" in name or "prize" in name:
        return ScamCategory.LOTTERY
    if "link" in name:
        return ScamCategory.PHISHING_LINK
    return ScamCategory.OTHER


async def extract_patterns(articles: List[Dict[str, Any]]) -> List[ScamPattern]:
    """
    Take raw news articles → ask LLM to convert each into ScamPattern JSON.
    """
    patterns: List[ScamPattern] = []

    for article in articles:
        prompt = PATTERN_PROMPT + "\n\nARTICLE:\n" + article["raw_text"]

        payload = {
            "system_instruction": "You are a scam pattern extractor.",
            "user": {"text": prompt},
        }

        try:
            src = await run_gemini(payload)
            # If run_gemini gave us {"raw_output": "..."} try to parse JSON
            if isinstance(src, dict) and "raw_output" in src:
                try:
                    src = json.loads(src["raw_output"])
                except json.JSONDecodeError:
                    continue
            if not isinstance(src, dict) or "scam_name" not in src:
                continue
        except Exception:
            continue

        pattern = ScamPattern(
            id=str(uuid.uuid4()),
            scam_name=src["scam_name"],
            category=_guess_category(src["scam_name"]),
            channel=src["channel"],
            modus_operandi=src["modus_operandi"],
            key_phrases=src["key_phrases"],
            red_flags=src["red_flags"],
            recommended_user_action=src["recommended_user_action"],
            example_message=src.get("example_message"),
            source_url=article.get("url"),
        )
        patterns.append(pattern)

    return patterns


def save_patterns(patterns: List[ScamPattern]) -> None:
    """
    Append new patterns into app/data/scam_patterns.json
    """
    db = Path(__file__).resolve().parents[2] / "data" / "scam_patterns.json"
    with open(db, "r+", encoding="utf-8") as f:
        stored = json.load(f)
        stored.extend([p.model_dump(mode="json") for p in patterns])
        f.seek(0)
        json.dump(stored, f, indent=2)
