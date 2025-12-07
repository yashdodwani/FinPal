"""
Scam Pipeline
-------------

Orchestrates:
1. risk_analyze  → fast pattern-based risk check
2. enrich_explanation → LLM to make the explanation human-friendly

This file provides:

- run(text, language)           → ScamAnalysisResult
- run_scam_pipeline(req)        → ScamAnalysisResult (used by master_agent)
"""

from app.schemas.scam import ScamAnalysisRequest, ScamAnalysisResult
from app.agents.scam.risk_analyzer import risk_analyze
from app.agents.scam.educator import enrich_explanation


async def run(text: str, language: str = "en") -> ScamAnalysisResult:
    """
    Original entrypoint: text + language → ScamAnalysisResult
    """
    req = ScamAnalysisRequest(text=text, language=language)
    base = risk_analyze(req)          # sync, very fast
    final = await enrich_explanation(base)
    return final


async def run_scam_pipeline(req: ScamAnalysisRequest) -> ScamAnalysisResult:
    """
    Async adapter used by the master agent.

    Keeps the same interface as loan / policy pipelines:
        await run_scam_pipeline(ScamAnalysisRequest) -> ScamAnalysisResult
    """
    return await run(req.text, req.language)
