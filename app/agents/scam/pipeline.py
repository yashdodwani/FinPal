"""
Scam Pipeline (Placeholder)
---------------------------

Real implementation will be provided by your teammate.
For now, we return a very simple ScamAnalysisResult so the app runs.
"""

from app.schemas import ScamAnalysisRequest, ScamAnalysisResult


async def run_scam_pipeline(request: ScamAnalysisRequest) -> ScamAnalysisResult:
    """
    Temporary stub implementation.
    Always returns a low-risk, 'not clearly a scam' response.
    """

    return ScamAnalysisResult(
        language=request.language,
        classification="uncertain_but_cautious",
        risk_score=0.3,
        is_scam=False,
        matched_patterns=[],
        red_flags=[
            "Scam analysis placeholder: real scam detection not yet implemented."
        ],
        recommended_action=(
            "Be cautious. Do not share OTP, PIN, or passwords. "
            "Verify with your bank using official channels."
        ),
        short_warning="Scam check is not fully enabled yet. Please be careful.",
        detailed_explanation=[
            "This is a temporary placeholder response.",
            "The full scam detection model is still being implemented.",
            "Until then, treat all unexpected messages with caution.",
        ],
    )
