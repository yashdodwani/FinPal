"""Types for master router agent."""
from enum import Enum
from pydantic import BaseModel

class MasterRoute(str, Enum):
    scam = "scam"
    loan = "loan"
    policy = "policy"

class RoutedPayload(BaseModel):
    route: MasterRoute
    payload: dict | None = None

