"""
Type models specific to the master routing agent.
"""

from pydantic import BaseModel, Field
from app.schemas.common import RouteEnum


class RouterDecision(BaseModel):
    """
    Clean structured output from the router LLM.
    """
    route: RouteEnum = Field(..., description="Chosen high-level route.")
    reason: str = Field(..., description="Short explanation why this route was selected.")
