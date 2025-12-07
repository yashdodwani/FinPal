import json
from app.schemas.scam import ScamAnalysisRequest, ScamAnalysisResult
from pathlib import Path


def load_patterns():
    # app/agents/scam/risk_analyzer.py -> app/data/scam_patterns.json
    path = Path(__file__).resolve().parents[2] / "data" / "scam_patterns.json"
    with open(path) as f:
        return json.load(f)


def risk_analyze(req: ScamAnalysisRequest) -> ScamAnalysisResult:
    patterns = load_patterns()
    msg = req.text.lower()

    matched = []
    red_flags = []

    for p in patterns:
        for phrase in p.get("key_phrases", []):
            if phrase.lower() in msg:
                matched.append(p["id"])
                red_flags.extend(p.get("red_flags", []))
                break

    if not matched:
        return ScamAnalysisResult(
            language=req.language,
            classification="probably safe",
            risk_score=0.2,
            is_scam=False,
            matched_patterns=[],
            red_flags=[],
            recommended_action="Proceed normally but stay cautious.",
            short_warning="Looks safe, but stay alert.",
            detailed_explanation=[
                "No strong scam indicators detected.",
                "Always avoid sharing OTP/PIN even if the sender claims to be bank support.",
            ],
        )

    # Use first matched pattern as primary
    primary = next(p for p in load_patterns() if p["id"] == matched[0])
    return ScamAnalysisResult(
        language=req.language,
        classification=primary["scam_name"],
        risk_score=0.9,
        is_scam=True,
        matched_patterns=matched,
        red_flags=red_flags,
        recommended_action=primary["recommended_user_action"],
        short_warning=f"⚠️ Suspicious: {primary['scam_name']}",
        detailed_explanation=[
            f"Modus Operandi: {primary['modus_operandi']}",
            f"Example message: {primary.get('example_message', 'N/A')}",
            *red_flags,
        ],
    )
