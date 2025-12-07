import json
from pathlib import Path
from typing import Any, Dict, List

from app.schemas.scam import ScamAnalysisRequest, ScamAnalysisResult


GENERIC_RECOMMENDED_ACTION = (
    "Never share OTP, PIN, CVV, or passwords with anyone. "
    "Do not click on suspicious links or QR codes. "
    "Verify the sender using official channels and report the incident to your bank "
    "and cybercrime portal if you suspect fraud."
)


def _patterns_path() -> Path:
    """
    Path to app/data/scam_patterns.json
    """
    return Path(__file__).resolve().parents[2] / "data" / "scam_patterns.json"


def load_patterns() -> List[Dict[str, Any]]:
    """
    Load scam patterns from JSON and NORMALIZE them into a common shape.

    Supports two shapes:
    1) Simple:
       {"name": "...", "description": "..."}
    2) Rich (ScamPattern-like):
       {"scam_name": "...", "key_phrases": [...], "red_flags": [...], ...}
    """

    path = _patterns_path()
    with open(path, encoding="utf-8") as f:
        raw: List[Dict[str, Any]] = json.load(f)

    normalized: List[Dict[str, Any]] = []

    for p in raw:
        # Rich format already
        if "scam_name" in p:
            scam_name = p["scam_name"]
            modus_operandi = p.get("modus_operandi") or p.get("description", "")
            key_phrases = p.get("key_phrases") or [scam_name]
            red_flags = p.get("red_flags") or [modus_operandi] if modus_operandi else []
            recommended = p.get("recommended_user_action") or GENERIC_RECOMMENDED_ACTION
            example = p.get("example_message") or ""
        # Simple format: name + description only
        else:
            scam_name = p.get("name", "Unknown Scam")
            modus_operandi = p.get("description", "")
            key_phrases = [scam_name]  # simple heuristic
            red_flags = [modus_operandi] if modus_operandi else []
            recommended = GENERIC_RECOMMENDED_ACTION
            example = ""

        normalized.append(
            {
                "scam_name": scam_name,
                "modus_operandi": modus_operandi,
                "key_phrases": key_phrases,
                "red_flags": red_flags,
                "recommended_user_action": recommended,
                "example_message": example,
            }
        )

    return normalized


def risk_analyze(req: ScamAnalysisRequest) -> ScamAnalysisResult:
    """
    Fast, non-LLM risk analyzer:

    - loads normalized patterns
    - checks if any key phrase appears in the message
    - if matches found → high risk
    - otherwise → probably safe
    """

    patterns = load_patterns()
    msg = req.text.lower()

    matched_indices: List[int] = []
    red_flags: List[str] = []

    for idx, p in enumerate(patterns):
        for phrase in p.get("key_phrases", []):
            phrase_l = phrase.lower().strip()
            if phrase_l and phrase_l in msg:
                matched_indices.append(idx)
                red_flags.extend(p.get("red_flags", []))
                break

    # No matches → low risk
    if not matched_indices:
        return ScamAnalysisResult(
            language=req.language,
            classification="probably safe",
            risk_score=0.2,
            is_scam=False,
            matched_patterns=[],
            red_flags=[],
            recommended_action=GENERIC_RECOMMENDED_ACTION,
            short_warning="Looks safe, but stay alert.",
            detailed_explanation=[
                "No strong scam indicators detected from the known pattern list.",
                "Still, never share OTP/PIN and always verify requests via official channels.",
            ],
        )

    # Use first matched pattern as "primary"
    primary = patterns[matched_indices[0]]

    scam_name = primary["scam_name"]
    modus_operandi = primary.get("modus_operandi", "")
    recommended = primary.get("recommended_user_action", GENERIC_RECOMMENDED_ACTION)
    example = primary.get("example_message", "")

    return ScamAnalysisResult(
        language=req.language,
        classification=scam_name,
        risk_score=0.9,
        is_scam=True,
        matched_patterns=[primary["scam_name"] for _ in matched_indices],
        red_flags=red_flags,
        recommended_action=recommended,
        short_warning=f"⚠️ Suspicious: {scam_name}",
        detailed_explanation=[
            f"Modus operandi: {modus_operandi}" if modus_operandi else "",
            *(red_flags or []),
            f"Example message: {example}" if example else "",
        ],
    )
