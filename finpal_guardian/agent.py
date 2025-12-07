from typing import Dict, Any

# ADK core agent class
from google.adk.agents import LlmAgent

# ✅ IMPORT YOUR BACKEND AGENTS & SCHEMAS HERE
# These lines connect ADK -> your actual multi-agent system
from app.schemas import UserRequest
from app.agents.master import route_request


# ---------------------------------------------------------
# TOOL: This is what ADK calls when a user sends a message
# ---------------------------------------------------------
async def finpal_guardian_tool(user_message: str, language: str = "en") -> Dict[str, Any]:
    """
    This function bridges ADK ↔ your existing Python multi-agent router.
    ADK calls this tool; the tool builds a UserRequest and sends it into
    your master agent (route_request).
    """

    req = UserRequest(
        text=user_message,
        language=language,
        route_hint=None,
        file_id=None,
        metadata={},
    )

    # 🔥 The real intelligence lives here:
    #    your router calls scam, loan, policy agents
    result = await route_request(req)

    # Convert Pydantic → dict so ADK can serialize it
    return result.model_dump()


# ---------------------------------------------------------
# ADK ROOT AGENT (UI-visible agent)
# ---------------------------------------------------------
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="finpal_guardian",
    description=(
        "FinPal Guardian - Multi-agent financial safety system that checks "
        "UPI scams, explains loan documents, and answers policy questions."
    ),
    instruction=(
        "You are FinPal Guardian.\n"
        "- For EVERY user message, you MUST call the tool 'finpal_guardian_tool'.\n"
        "- Pass the message text as user_message.\n"
        "- Wait for the tool result and then summarize the structured output "
        "in simple language.\n"
        "- If the tool returns warnings or recommended actions, ALWAYS show them."
    ),
    tools=[finpal_guardian_tool],
)
