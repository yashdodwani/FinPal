import os
import json
import uuid
import google.generativeai as genai

from schemas.scam import ScamPattern, ScamCategory

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PATTERN_PROMPT_PATH = "scam/prompts/pattern_prompt.txt"
with open(PATTERN_PROMPT_PATH) as f:
    PATTERN_PROMPT = f.read()


def _guess_category(name: str) -> ScamCategory:
    name = name.lower()
    if "refund" in name: return ScamCategory.UPI_REFUND
    if "kyc" in name: return ScamCategory.KYC_VERIFICATION
    if "otp" in name: return ScamCategory.OTP_PHISHING
    if "investment" in name: return ScamCategory.INVESTMENT
    if "lottery" in name or "prize" in name: return ScamCategory.LOTTERY
    if "link" in name: return ScamCategory.PHISHING_LINK
    return ScamCategory.OTHER


def extract_patterns(articles):
    model = genai.GenerativeModel("gemini-2.0-pro")
    patterns = []

    for article in articles:
        prompt = PATTERN_PROMPT + "\n\nARTICLE:\n" + article["raw_text"]
        out = model.generate_content(prompt).text

        try:
            src = json.loads(out)
        except:
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


def save_patterns(patterns):
    db = "backend/database/patterns.json"
    with open(db, "r+") as f:
        stored = json.load(f)
        stored.extend([p.model_dump() for p in patterns])
        f.seek(0)
        json.dump(stored, f, indent=2)
