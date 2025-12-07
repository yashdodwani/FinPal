"""
Master Router Agent
-------------------

This agent receives a UserRequest and determines which pipeline
to execute: Scam, Loan, or Policy.

It uses:
- Optional route_hint from the UserRequest
- LLM-based intent classification (router_prompt.txt)
- Returns a unified AgentResponse

NOTE: Right now this is a plain Python orchestrator.
To integrate with Google ADK, you can wrap `route_request` in an ADK LlmAgent
and use `adk web` to inspect it visually.
"""

import json
from pathlib import Path
from typing import Any, Dict

from app.schemas import (
    UserRequest,
    AgentResponse,
    AgentError,
    RouteEnum,
    LoanIngestionRequest,
    PolicyQARequest,
    ScamAnalysisRequest,
)
from app.core.gemini import run_gemini
from app.agents.loan.pipeline import run_loan_pipeline
from app.agents.policy.pipeline import run_policy_pipeline
from app.agents.scam.pipeline import run_scam_pipeline  # placeholder for teammate

from .types import RouterDecision

ROUTER_PROMPT_PATH = Path("app/agents/master/router_prompt.txt")


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


async def route_request(user_req: UserRequest) -> AgentResponse:
    """
    Main entry point used by FastAPI.

    1. Uses route_hint if provided.
    2. Otherwise calls classify_route().
    3. Calls the appropriate pipeline.
    """

    try:
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
            payload = ScamAnalysisRequest(
                text=user_req.text or "",
                language=user_req.language,
                url=user_req.metadata.get("url"),
                upi_id=user_req.metadata.get("upi_id"),
                channel=user_req.metadata.get("channel"),
            )
            result = await run_scam_pipeline(payload)

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
        # Catch-all failure
        return AgentResponse(
            final_route=user_req.route_hint or RouteEnum.SCAM_CHECK,
            data=None,
            error=AgentError(message=str(exc)),
            debug_info={"router_failed": True},
        )
