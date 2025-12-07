"""Master router agent.

Routes to scam/loan/policy based on intent. Currently a stub.
"""
from app.schemas.common import UserRequest, AgentResponse, RouteEnum

async def route_request(request: UserRequest) -> AgentResponse:
    """Stub router that returns a TODO response.

    TODO: Implement intent detection and route to appropriate agent graph.
    """
    return AgentResponse(route=request.route_hint or RouteEnum.guardian, result={"echo": request.text}, status="todo")

