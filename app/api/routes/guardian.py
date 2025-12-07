"""Guardian route: entrypoint to master agent router."""
from fastapi import APIRouter
from app.schemas.common import UserRequest, AgentResponse
from app.agents.master.master_agent import route_request

router = APIRouter()

@router.post("/guardian", response_model=AgentResponse)
async def guardian_endpoint(payload: UserRequest) -> AgentResponse:
    """POST /guardian -> calls master agent routing stub."""
    return await route_request(payload)

