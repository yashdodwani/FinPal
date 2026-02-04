"""
Honeypot API Endpoint
---------------------

Dedicated endpoint for honeypot interactions.
This is the primary interface for scammer engagement.

Endpoints:
- POST /honeypot - Handle incoming scammer message
- GET /honeypot/status/{session_id} - Get session status (debug only)
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.honeypot import HoneypotRequest, HoneypotResponse
from app.agents.honeypot.pipeline import (
    handle_honeypot_message,
    get_session_status,
    init_honeypot_session,
)

router = APIRouter()


@router.post("/honeypot", response_model=HoneypotResponse, tags=["honeypot"])
async def honeypot_endpoint(request: HoneypotRequest) -> HoneypotResponse:
    """
    Main honeypot endpoint for scammer engagement.
    
    This endpoint:
    - Accepts scammer messages
    - Returns human-like responses
    - Silently extracts intelligence
    - Maintains multi-turn conversation state
    - Sends callback when engagement completes
    
    Request:
    - session_id: Unique identifier for the conversation
    - text: Scammer's message
    - language: Language code (default: "en")
    - metadata: Optional additional context
    
    Response:
    - status: "success" (always, to maintain cover)
    - reply: Human-like response message
    
    NOTE: This endpoint NEVER reveals that scam detection occurred.
    The response always appears as a normal confused human reply.
    """
    
    response = await handle_honeypot_message(request)
    return response


@router.get("/honeypot/status/{session_id}", tags=["honeypot"])
async def honeypot_status(session_id: str) -> dict:
    """
    Get current status of a honeypot session.
    
    DEBUG ONLY - Remove or protect in production.
    
    Returns:
    - session_id
    - stage
    - message_count
    - persona
    - intelligence_summary
    - callback_sent
    """
    
    status = await get_session_status(session_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return status


@router.post("/honeypot/init/{session_id}", tags=["honeypot"])
async def init_session(
    session_id: str,
    confidence: float = 0.9,
    scam_type: Optional[str] = None
) -> dict:
    """
    Initialize a new honeypot session.
    
    DEBUG ONLY - Normally sessions are auto-created on first message.
    
    Parameters:
    - session_id: Unique session identifier
    - confidence: Initial scam confidence (default: 0.9)
    - scam_type: Optional scam classification
    
    Returns session initialization confirmation.
    """
    
    session = await init_honeypot_session(
        session_id=session_id,
        initial_scam_confidence=confidence,
        scam_type=scam_type
    )
    
    return {
        "session_id": session.session_id,
        "initialized": True,
        "persona": session.persona_name,
        "stage": session.stage.value
    }
