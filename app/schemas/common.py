"""Shared Pydantic models and enums used across agents and API."""
from enum import Enum
from pydantic import BaseModel

class RouteEnum(str, Enum):
    guardian = "guardian"
    loan = "loan"
    policy = "policy"
    scam = "scam"

class UserRequest(BaseModel):
    """Generic user request payload."""
    text: str | None = None
    route_hint: RouteEnum | None = None

class AgentResponse(BaseModel):
    """Generic agent response payload."""
    route: RouteEnum | None = None
    result: dict | None = None
    status: str = "todo"

