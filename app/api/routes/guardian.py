from fastapi import APIRouter, Depends

from app.schemas import UserRequest, AgentResponse
from app.agents.master import route_request

router = APIRouter()


@router.post("/guardian", response_model=AgentResponse, tags=["guardian"])
async def guardian_endpoint(
    request: UserRequest,
) -> AgentResponse:
    """
    Main entrypoint for the Financial Safety Net.

    - Accepts a generic UserRequest
    - Delegates to the master agent
    - Returns an AgentResponse (with final_route + data)
    """
    response = await route_request(request)
    return response
