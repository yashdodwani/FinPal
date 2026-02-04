"""
Honeypot Pipeline
-----------------

Main orchestrator for the honeypot engagement system.

Flow:
1. Get/create session state
2. Extract intelligence from scammer message
3. Select engagement strategy
4. Generate persona response
5. Update session state
6. Check exit conditions
7. Send callback if exiting

This pipeline is called by both:
- Direct honeypot endpoint (/honeypot)
- Master agent router (when scam detected with high confidence)
"""

import logging
from typing import Optional

from app.schemas.honeypot import (
    HoneypotRequest,
    HoneypotResponse,
    HoneypotSessionState,
    EngagementStage,
    ExtractedIntelligence,
)
from app.schemas.scam import ScamAnalysisRequest

from .session_manager import get_session_manager
from .intelligence_extractor import (
    extract_intelligence,
    has_valuable_intelligence,
    summarize_intelligence,
)
from .persona_engine import (
    select_strategy,
    generate_response,
    generate_exit_response,
    detect_info_requests,
)
from .callback_reporter import send_callback_with_retry

logger = logging.getLogger(__name__)


async def should_trigger_honeypot(
    scam_result: "ScamAnalysisRequest",
    confidence_threshold: float = 0.7
) -> bool:
    """
    Determine if honeypot should be triggered based on scam detection results.
    This is called by the master agent during routing.
    """
    # Import here to avoid circular imports
    from app.agents.scam.risk_analyzer import risk_analyze
    from app.schemas.scam import ScamAnalysisRequest
    
    # If scam_result is a request, analyze it
    if isinstance(scam_result, ScamAnalysisRequest):
        analysis = risk_analyze(scam_result)
        return analysis.is_scam and analysis.risk_score >= confidence_threshold
    
    # If it's already a result
    return getattr(scam_result, 'is_scam', False) and \
           getattr(scam_result, 'risk_score', 0) >= confidence_threshold


async def handle_honeypot_message(request: HoneypotRequest) -> HoneypotResponse:
    """
    Main entry point for honeypot message handling.
    Called for each scammer message in the conversation.
    
    Returns a clean HoneypotResponse with only status and reply.
    """
    
    session_manager = get_session_manager()
    
    # 1. Get or create session
    session = await session_manager.get_or_create_session(request.session_id)
    
    logger.info(
        f"Honeypot handling message for session {request.session_id}, "
        f"stage: {session.stage.value}, turn: {len(session.messages) + 1}"
    )
    
    # 2. Extract intelligence from scammer message (silently)
    new_intel = await extract_intelligence(
        scammer_message=request.text,
        conversation_history=session.messages,
        use_llm=True
    )
    
    # 3. Accumulate intelligence
    if has_valuable_intelligence(new_intel):
        await session_manager.accumulate_intelligence(request.session_id, new_intel)
        await session_manager.reset_stagnant_turns(request.session_id)
        logger.info(f"Extracted intelligence: {summarize_intelligence(new_intel)}")
    else:
        stagnant = await session_manager.increment_stagnant_turns(request.session_id)
        logger.debug(f"No new intel this turn. Stagnant turns: {stagnant}")
    
    # 4. Record scammer message
    await session_manager.add_message(
        session_id=request.session_id,
        role="scammer",
        content=request.text,
        extracted=new_intel
    )
    
    # 5. Detect what info scammer is requesting
    info_requests = detect_info_requests(request.text)
    if info_requests:
        current_session = await session_manager.get_session(request.session_id)
        if current_session:
            current_session.information_requested_by_scammer.extend(info_requests)
            current_session.information_requested_by_scammer = list(set(
                current_session.information_requested_by_scammer
            ))
            await session_manager.update_session(current_session)
    
    # Refresh session after updates - this should always exist as we created it above
    session = await session_manager.get_session(request.session_id)
    if not session:
        logger.error(f"Session {request.session_id} not found after creation")
        return HoneypotResponse(status="success", reply="Sorry, I didn't understand that...")
    
    # 6. Select strategy and check for stage transitions
    strategy, new_stage, should_exit, exit_reason = await select_strategy(
        session=session,
        scammer_message=request.text
    )
    
    # Update stage if changed
    if new_stage != session.stage:
        await session_manager.update_stage(request.session_id, new_stage)
        logger.info(f"Stage transition: {session.stage.value} -> {new_stage.value}")
    
    # 7. Check forced exit conditions
    forced_exit = False
    if len(session.messages) >= session.max_turns:
        forced_exit = True
        exit_reason = "Max turns reached"
    elif session.turns_without_progress >= 5:
        forced_exit = True
        exit_reason = "Conversation stagnating"
    
    # 8. Generate response
    if should_exit or forced_exit or new_stage == EngagementStage.EXIT:
        # Exit gracefully
        reply = generate_exit_response(session, exit_reason or "engagement complete")
        
        # Update stage to EXIT
        await session_manager.update_stage(request.session_id, EngagementStage.EXIT)
        
        # Record our exit message
        await session_manager.add_message(
            session_id=request.session_id,
            role="honeypot",
            content=reply
        )
        
        # Get final session state
        final_session = await session_manager.get_session(request.session_id)
        
        # Send callback (async, don't block response)
        logger.info(f"Ending engagement for session {request.session_id}. Reason: {exit_reason}")
        
        # Send callback with retry
        if final_session:
            callback_success = await send_callback_with_retry(final_session)
            if not callback_success:
                logger.error(f"CRITICAL: Failed to send callback for session {request.session_id}")
        
        return HoneypotResponse(status="success", reply=reply)
    
    # Normal response generation
    reply = await generate_response(
        session=session,
        scammer_message=request.text,
        strategy=strategy
    )
    
    # Record our response
    await session_manager.add_message(
        session_id=request.session_id,
        role="honeypot",
        content=reply
    )
    
    logger.debug(f"Generated reply with strategy {strategy.value}: {reply[:100]}...")
    
    return HoneypotResponse(status="success", reply=reply)


async def run_honeypot_pipeline(request: HoneypotRequest) -> HoneypotResponse:
    """
    Alias for handle_honeypot_message.
    Used by master agent router for consistency with other pipelines.
    """
    return await handle_honeypot_message(request)


async def init_honeypot_session(
    session_id: str,
    initial_scam_confidence: float = 0.9,
    scam_type: Optional[str] = None
) -> HoneypotSessionState:
    """
    Initialize a new honeypot session with known scam context.
    Called by master agent when routing to honeypot.
    """
    
    session_manager = get_session_manager()
    session = await session_manager.get_or_create_session(session_id)
    
    # Set scam context
    session.scam_confidence = initial_scam_confidence
    session.scam_type_detected = scam_type
    
    await session_manager.update_session(session)
    
    logger.info(
        f"Initialized honeypot session {session_id} with "
        f"confidence {initial_scam_confidence}, type: {scam_type}"
    )
    
    return session


async def get_session_status(session_id: str) -> Optional[dict]:
    """
    Get current session status (for debugging/monitoring).
    """
    
    session_manager = get_session_manager()
    session = await session_manager.get_session(session_id)
    
    if not session:
        return None
    
    return {
        "session_id": session.session_id,
        "stage": session.stage.value,
        "message_count": len(session.messages),
        "persona": session.persona_name,
        "intelligence_summary": summarize_intelligence(session.accumulated_intelligence),
        "stagnant_turns": session.turns_without_progress,
        "callback_sent": session.callback_sent,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }
