"""
Master Router Agent
-------------------

This agent receives a UserRequest and determines which pipeline
to execute: Scam, Loan, or Policy.

It uses:
- Optional route_hint from the UserRequest
- LLM-based intent classification (router_prompt.txt)
- Returns a unified AgentResponse
"""

from typing import Dict, Any

from app.schemas import (
    UserRequest,
    AgentResponse,
    AgentError,
    RouteEnum,
    LoanIngestionRequest,
    PolicyQARequest,
    ScamAnalysisRequest,
)

from .types import RouterDecision
from app.core.gemini import run_gemini
from app.agents.loan.pipeline import run_loan_pipeline
from app.agents.policy.pipeline import run_policy_pipeline
from app.agents.scam.pipeline import run_scam_pipeline


ROUTER_PROMPT_PATH = "app/agents/master/router_prompt.txt"


async def load_router_prompt() -> str:
    """Load router system prompt from file."""
    with open(ROUTER_PROMPT_PATH, "r") as f:
        return f.read()


async def classify_route(user_req: UserRequest) -> RouterDecision:
    """
    Uses Gemini to classify the user's intent.
    Returns a RouterDecision(route: RouteEnum, reason: str).
    """

    prompt = await load_router_prompt()

    llm_input = {
        "system_instruction": prompt,
        "user": {
            "text": user_req.text,
            "metadata": user_req.metadata,
        },
    }

    llm_output = await run_gemini(llm_input)

    try:
        parsed = RouterDecision.model_validate(llm_output)  # ensures type safety
        return parsed
    except Exception as e:
        raise ValueError(f"RouterDecision parsing failed: {e}")


async def route_request(user_req: UserRequest) -> AgentResponse:
    """
    Main entry point.
    1. Uses route_hint if provided.
    2. Otherwise calls classify_route().
    3. Calls the appropriate pipeline.
    """

    try:
        # 1. Use user-provided hint if available
        if user_req.route_hint:
            final_route = user_req.route_hint
            reason = "Used route_hint"
        else:
            # 2. Otherwise classify with LLM
            decision = await classify_route(user_req)
            final_route = decision.route
            reason = decision.reason

        # 3. Dispatch pipeline
        if final_route == RouteEnum.LOAN_DOC:
            payload = LoanIngestionRequest(
                language=user_req.language,
                source={"file_id": user_req.file_id, "text_content": user_req.text},
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
                error=AgentError(message="Unknown route"),
                debug_info={"reason": reason},
            )

        # Success
        return AgentResponse(
            final_route=final_route,
            data=result,
            debug_info={"router_reason": reason},
        )

    except Exception as e:
        # Catch-all failure
        return AgentResponse(
            final_route=user_req.route_hint or RouteEnum.SCAM_CHECK,
            data=None,
            error=AgentError(message=str(e)),
        )
