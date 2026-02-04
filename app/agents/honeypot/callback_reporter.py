"""
Callback Reporter
-----------------

Sends final honeypot results to the evaluation endpoint.
Ensures callback is sent exactly once per session.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from app.schemas.honeypot import (
    HoneypotSessionState,
    HoneypotCallbackPayload,
    ExtractedIntelligence,
)
from .session_manager import get_session_manager
from .intelligence_extractor import summarize_intelligence

logger = logging.getLogger(__name__)

# Evaluation endpoint
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
CALLBACK_TIMEOUT = 30.0  # seconds


def generate_agent_notes(session: HoneypotSessionState) -> str:
    """Generate a brief behavioral summary of the engagement."""
    
    total_turns = len(session.messages)
    scammer_msgs = [m for m in session.messages if m.role == "scammer"]
    honeypot_msgs = [m for m in session.messages if m.role == "honeypot"]
    
    intel = session.accumulated_intelligence
    intel_items = []
    if intel.upi_ids:
        intel_items.append(f"{len(intel.upi_ids)} UPI ID(s)")
    if intel.bank_accounts:
        intel_items.append(f"{len(intel.bank_accounts)} bank account(s)")
    if intel.phishing_urls:
        intel_items.append(f"{len(intel.phishing_urls)} URL(s)")
    if intel.phone_numbers:
        intel_items.append(f"{len(intel.phone_numbers)} phone number(s)")
    if intel.app_names:
        intel_items.append(f"apps: {', '.join(intel.app_names)}")
    
    intel_summary = ", ".join(intel_items) if intel_items else "minimal intelligence"
    
    # Determine scam category
    scam_type = session.scam_type_detected or "Unknown"
    if not session.scam_type_detected and intel.scam_keywords:
        # Infer from keywords
        keywords_lower = [k.lower() for k in intel.scam_keywords]
        if any("otp" in k or "pin" in k for k in keywords_lower):
            scam_type = "OTP/PIN Phishing"
        elif any("upi" in k or "refund" in k for k in keywords_lower):
            scam_type = "UPI Refund Scam"
        elif any("kyc" in k for k in keywords_lower):
            scam_type = "KYC Verification Scam"
        elif any("remote" in k or "anydesk" in k for k in keywords_lower):
            scam_type = "Remote Access Scam"
        elif any("lottery" in k or "prize" in k for k in keywords_lower):
            scam_type = "Lottery/Prize Scam"
    
    # Calculate duration if possible
    if session.messages:
        first_msg = session.messages[0].timestamp
        last_msg = session.messages[-1].timestamp
        duration_secs = int((last_msg - first_msg).total_seconds())
        duration_str = f"{duration_secs // 60}m {duration_secs % 60}s"
    else:
        duration_str = "unknown"
    
    # Build notes
    notes = (
        f"Scam Type: {scam_type}. "
        f"Engagement: {total_turns} messages over {duration_str}. "
        f"Persona: {session.persona_name} ({session.persona_context.get('occupation', 'unknown')}). "
        f"Extracted: {intel_summary}. "
        f"Info requested by scammer: {', '.join(session.information_requested_by_scammer[:5]) or 'none recorded'}. "
        f"Exit stage: {session.stage.value}."
    )
    
    return notes


def build_callback_payload(session: HoneypotSessionState) -> HoneypotCallbackPayload:
    """Build the callback payload from session state."""
    
    # Calculate duration
    duration_secs: Optional[int] = None
    if len(session.messages) >= 2:
        first_msg = session.messages[0].timestamp
        last_msg = session.messages[-1].timestamp
        duration_secs = int((last_msg - first_msg).total_seconds())
    
    return HoneypotCallbackPayload(
        sessionId=session.session_id,
        scamDetected=True,
        totalMessagesExchanged=len(session.messages),
        extractedIntelligence=session.accumulated_intelligence,
        agentNotes=generate_agent_notes(session),
        scamType=session.scam_type_detected,
        engagementDuration=duration_secs,
        confidenceScore=session.scam_confidence
    )


async def send_callback(session: HoneypotSessionState) -> bool:
    """
    Send final callback to evaluation endpoint.
    
    Returns True if callback was sent successfully.
    Returns False if already sent or if sending failed.
    """
    
    # Check if already sent
    if session.callback_sent:
        logger.warning(f"Callback already sent for session {session.session_id}")
        return False
    
    # Build payload
    payload = build_callback_payload(session)
    
    # Convert to dict for JSON serialization
    # Handle nested Pydantic models
    payload_dict = {
        "sessionId": payload.sessionId,
        "scamDetected": payload.scamDetected,
        "totalMessagesExchanged": payload.totalMessagesExchanged,
        "extractedIntelligence": {
            "bank_accounts": payload.extractedIntelligence.bank_accounts,
            "upi_ids": payload.extractedIntelligence.upi_ids,
            "phishing_urls": payload.extractedIntelligence.phishing_urls,
            "phone_numbers": payload.extractedIntelligence.phone_numbers,
            "email_addresses": payload.extractedIntelligence.email_addresses,
            "scam_keywords": payload.extractedIntelligence.scam_keywords,
            "app_names": payload.extractedIntelligence.app_names,
            "payment_requests": payload.extractedIntelligence.payment_requests,
        },
        "agentNotes": payload.agentNotes,
        "scamType": payload.scamType,
        "engagementDuration": payload.engagementDuration,
        "confidenceScore": payload.confidenceScore,
    }
    
    logger.info(f"Sending callback for session {session.session_id}")
    logger.debug(f"Callback payload: {payload_dict}")
    
    try:
        async with httpx.AsyncClient(timeout=CALLBACK_TIMEOUT) as client:
            response = await client.post(
                CALLBACK_URL,
                json=payload_dict,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(
                    f"Callback sent successfully for session {session.session_id}. "
                    f"Status: {response.status_code}"
                )
                
                # Mark as sent in session manager
                session_manager = get_session_manager()
                await session_manager.mark_callback_sent(session.session_id)
                
                return True
            else:
                logger.error(
                    f"Callback failed for session {session.session_id}. "
                    f"Status: {response.status_code}, Body: {response.text}"
                )
                return False
                
    except httpx.TimeoutException:
        logger.error(f"Callback timeout for session {session.session_id}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Callback request error for session {session.session_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected callback error for session {session.session_id}: {e}")
        return False


async def send_callback_with_retry(
    session: HoneypotSessionState,
    max_retries: int = 3
) -> bool:
    """
    Send callback with retry logic.
    """
    
    for attempt in range(max_retries):
        success = await send_callback(session)
        if success:
            return True
        
        if attempt < max_retries - 1:
            import asyncio
            wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
            logger.info(f"Retrying callback in {wait_time}s (attempt {attempt + 2}/{max_retries})")
            await asyncio.sleep(wait_time)
    
    logger.error(f"All callback attempts failed for session {session.session_id}")
    return False
