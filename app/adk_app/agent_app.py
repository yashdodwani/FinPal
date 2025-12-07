"""
ADK Agent App
-------------
This file creates an ADK-ready agent that wraps your existing
Python master agent logic (`route_request`).

After saving this, you can run:

    adk web app/adk_app/agent_app:root_agent

This will launch the ADK UI and render:
 - request schema automatically from Pydantic (UserRequest)
 - responses from AgentResponse
 - logs
 - evaluation / testing tools
"""

from google import adk
from pydantic import BaseModel

from app.schemas import UserRequest, AgentResponse
from app.agents.master import route_request


class RootAgent(adk.Agent):
    """
    ADK-compatible wrapper around your master agent.
    ADK expects:
      - run(self, input: InputModel) -> OutputModel
    """

    name = "financial_safety_root_agent"
    description = (
        "Master router agent orchestrates: scam check, "
        "loan explanation, policy QA."
    )

    # ADK inspects these two fields to auto-generate UI & types
    input_schema = UserRequest
    output_schema = AgentResponse

    async def run(self, input: UserRequest) -> AgentResponse:
        """
        ADK calls this method when user triggers request in the web UI.
        """
        response = await route_request(input)
        return response


# This is what ADK will import:
#   adk web app/adk_app/agent_app:root_agent
root_agent = RootAgent()
