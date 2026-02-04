"""
Master Router Agent
-------------------

This agent receives a UserRequest and determines which pipeline
to execute: Scam, Loan, Policy, or Honeypot.

It uses:
- Optional route_hint from the UserRequest
- LLM-based intent classification (router_prompt.txt)
- Silent scam detection to trigger honeypot mode
- Returns a unified AgentResponse

HONEYPOT MODE:
When scam is detected with high confidence:
1. Detection is SILENT (not surfaced to response)
2. Control is handed to honeypot agent
3. Response appears as normal human reply

NOTE: Right now this is a plain Python orchestrator.
To integrate with Google ADK, you can wrap `route_request` in an ADK LlmAgent
and use `adk web` to inspect it visually.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import uuid

from app.schemas import (
    UserRequest,
    AgentResponse,
    AgentError,
    RouteEnum,
    LoanIngestionRequest,
    PolicyQARequest,
    ScamAnalysisRequest,
)
from app.schemas.honeypot import HoneypotRequest, HoneypotResponse
from app.core.gemini import run_gemini
from app.agents.loan.pipeline import run_loan_pipeline
from app.agents.policy.pipeline import run_policy_pipeline
from app.agents.scam.pipeline import run_scam_pipeline
from app.agents.scam.risk_analyzer import risk_analyze
from app.agents.honeypot.pipeline import (
    run_honeypot_pipeline,
    init_honeypot_session,
)

from .types import RouterDecision

logger = logging.getLogger(__name__)

ROUTER_PROMPT_PATH = Path("app/agents/master/router_prompt.txt")

# Honeypot activation threshold
HONEYPOT_CONFIDENCE_THRESHOLD = 0.7


def _load_router_prompt() -> str:
    return ROUTER_PROMPT_PATH.read_text(encoding="utf-8")


async def classify_route(user_req: UserRequest) -> RouterDecision:
    """
    Uses Gemini 3 to classify the user's intent.
    Returns a RouterDecision(route: RouteEnum, reason: str).

    Handles both:
    - dict outputs from run_gemini
    - {"raw_output": "<json string>"} fallback
    """

    prompt = _load_router_prompt()

    payload: Dict[str, Any] = {
        "system_instruction": prompt,
        "user": {
            "text": user_req.text,
            "metadata": user_req.metadata,
        },
    }

    llm_output = await run_gemini(payload)

    if "error" in llm_output:
        raise RuntimeError(f"Router LLM error: {llm_output['error']}")

    if "raw_output" in llm_output:
        # LLM returned a JSON string we need to parse
        try:
            parsed = json.loads(llm_output["raw_output"])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse router JSON: {exc}") from exc
    else:
        parsed = llm_output

    return RouterDecision.model_validate(parsed)


def _silent_scam_check(text: str, language: str = "en") -> tuple[bool, float, Optional[str]]:
    """
    Perform silent scam detection.
    Returns: (is_scam, confidence, scam_type)
    
    This NEVER surfaces in user-visible responses.
    """
    
    if not text:
        return False, 0.0, None
    
    req = ScamAnalysisRequest(text=text, language=language)
    result = risk_analyze(req)
    
    return result.is_scam, result.risk_score, result.classification


async def route_request(
    user_req: UserRequest,
    session_id: Optional[str] = None,
    honeypot_mode: bool = False
) -> AgentResponse:
    """
    Main entry point used by FastAPI.

    1. Uses route_hint if provided.
    2. Otherwise calls classify_route().
    3. For SCAM_CHECK route, silently checks if honeypot should activate.
    4. Calls the appropriate pipeline.
    
    Parameters:
    - user_req: The user's request
    - session_id: Optional session ID for honeypot tracking
    - honeypot_mode: If True, forces honeypot mode (used by honeypot endpoint)
    """

    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = user_req.metadata.get("session_id") or str(uuid.uuid4())
        
        # HONEYPOT MODE: Direct routing when explicitly requested
        if honeypot_mode or user_req.route_hint == RouteEnum.HONEYPOT:
            return await _handle_honeypot_route(user_req, session_id)
        
        # 1. Use user-provided hint if available
        if user_req.route_hint:
            final_route = user_req.route_hint
            reason = "Used route_hint provided by client."
        else:
            # 2. Otherwise classify with LLM
            decision = await classify_route(user_req)
            final_route = decision.route
            reason = decision.reason

        # 3. Dispatch to the selected pipeline
        if final_route == RouteEnum.LOAN_DOC:
            payload = LoanIngestionRequest(
                language=user_req.language,
                source={
                    "file_id": user_req.file_id,
                    "text_content": user_req.text,
                },
            )
            result = await run_loan_pipeline(payload)

        elif final_route == RouteEnum.POLICY_QA:
            payload = PolicyQARequest(
                question=user_req.text or "",
                language=user_req.language,
            )
            result = await run_policy_pipeline(payload)

        elif final_route == RouteEnum.SCAM_CHECK:
            # CRITICAL: Silent scam check for honeypot activation
            is_scam, confidence, scam_type = _silent_scam_check(
                user_req.text or "",
                user_req.language
            )
            
            # If high-confidence scam detected, SILENTLY route to honeypot
            if is_scam and confidence >= HONEYPOT_CONFIDENCE_THRESHOLD:
                logger.info(
                    f"Honeypot activated: confidence={confidence:.2f}, "
                    f"type={scam_type}, session={session_id}"
                )
                
                # Initialize honeypot session with scam context
                await init_honeypot_session(
                    session_id=session_id,
                    initial_scam_confidence=confidence,
                    scam_type=scam_type
                )
                
                return await _handle_honeypot_route(user_req, session_id)
            
            # Low confidence scam or not a scam - return normal analysis
            # (This path is for legitimate users checking suspicious messages)
            payload = ScamAnalysisRequest(
                text=user_req.text or "",
                language=user_req.language,
                url=user_req.metadata.get("url"),
                upi_id=user_req.metadata.get("upi_id"),
                channel=user_req.metadata.get("channel"),
            )
            result = await run_scam_pipeline(payload)

        elif final_route == RouteEnum.HONEYPOT:
            return await _handle_honeypot_route(user_req, session_id)

        else:
            return AgentResponse(
                final_route=final_route,
                data=None,
                error=AgentError(message="Unknown route selected by router."),
                debug_info={"reason": reason},
            )

        # Success
        return AgentResponse(
            final_route=final_route,
            data=result,
            debug_info={"router_reason": reason},
        )

    except Exception as exc:
        logger.exception(f"Router error: {exc}")
        # Catch-all failure
        return AgentResponse(
            final_route=user_req.route_hint or RouteEnum.SCAM_CHECK,
            data=None,
            error=AgentError(message=str(exc)),
            debug_info={"router_failed": True},
        )


async def _handle_honeypot_route(
    user_req: UserRequest,
    session_id: str
) -> AgentResponse:
    """
    Handle honeypot routing internally.
    Returns response in AgentResponse format with honeypot data.
    """
    
    honeypot_req = HoneypotRequest(
        session_id=session_id,
        text=user_req.text or "",
        language=user_req.language,
        metadata=user_req.metadata
    )
    
    honeypot_response = await run_honeypot_pipeline(honeypot_req)
    
    # Return as AgentResponse
    # Note: For honeypot, we return a clean response
    # The actual route is hidden - it appears as a normal reply
    return AgentResponse(
        final_route=RouteEnum.HONEYPOT,
        data=honeypot_response.model_dump(),
        debug_info=None  # No debug info in honeypot mode - prevent leakage
    )
