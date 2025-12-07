from app.schemas.scam import ScamAnalysisRequest, ScamAnalysisResult
from app.agents.scam.risk_analyzer import risk_analyze
from app.agents.scam.educator import enrich_explanation


def run(text: str, language: str = "en") -> dict:
    """
    Original synchronous entrypoint.
    Used by Streamlit / manual callers.
    """
    req = ScamAnalysisRequest(text=text, language=language)
    base = risk_analyze(req)
    final = enrich_explanation(base)
    return final.model_dump()

async def run_scam_pipeline(req: ScamAnalysisRequest) -> dict:
    """
    Async adapter so master_agent can call scam pipeline without changes.
    """
    result = run(req.text, req.language)  # call existing sync pipeline
    return ScamAnalysisResult(**result).model_dump()     # schema-safe for AgentResponse
