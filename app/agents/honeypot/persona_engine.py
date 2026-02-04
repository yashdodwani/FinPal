"""
Persona Engine
--------------

Generates believable human-like responses for honeypot engagement.
Maintains persona consistency across conversation turns.
"""

import json
from typing import List, Optional

from app.schemas.honeypot import (
    HoneypotSessionState,
    EngagementStage,
    EngagementStrategy,
    ConversationMessage,
)
from app.core.gemini import run_gemini
from .prompts import get_persona_prompt, get_strategy_prompt
from .intelligence_extractor import summarize_intelligence


async def select_strategy(
    session: HoneypotSessionState,
    scammer_message: str
) -> tuple[EngagementStrategy, EngagementStage, bool, Optional[str]]:
    """
    Select engagement strategy and determine stage transitions.
    Returns: (strategy, new_stage, should_exit, exit_reason)
    """
    
    # Build intel summary
    intel_summary = summarize_intelligence(session.accumulated_intelligence)
    
    prompt = get_strategy_prompt().format(
        stage=session.stage.value,
        message_count=len(session.messages),
        stagnant_turns=session.turns_without_progress,
        info_requested=", ".join(session.information_requested_by_scammer) or "None yet",
        intel_summary=intel_summary,
        scammer_message=scammer_message
    )
    
    payload = {
        "system_instruction": prompt,
        "user": {"analyze": scammer_message}
    }
    
    try:
        result = await run_gemini(payload)
        
        if "raw_output" in result:
            parsed = json.loads(result["raw_output"])
        elif "error" in result:
            # Default strategy on error
            return (
                EngagementStrategy.ASK_CLARIFICATION,
                session.stage,
                False,
                None
            )
        else:
            parsed = result
        
        strategy = EngagementStrategy(parsed.get("recommended_strategy", "ask_clarification"))
        new_stage = EngagementStage(parsed.get("new_stage", session.stage.value))
        should_exit = parsed.get("should_exit", False)
        exit_reason = parsed.get("exit_reason")
        
        return strategy, new_stage, should_exit, exit_reason
        
    except Exception:
        # Fallback to safe defaults
        return (
            EngagementStrategy.PRETEND_CONFUSION,
            session.stage,
            False,
            None
        )


def format_conversation_history(messages: List[ConversationMessage], limit: int = 10) -> str:
    """Format recent conversation history for prompt."""
    
    if not messages:
        return "This is the first message."
    
    recent = messages[-limit:]
    lines = []
    
    for msg in recent:
        role = "THEM" if msg.role == "scammer" else "YOU ({name})"
        lines.append(f"{role}: {msg.content}")
    
    return "\n".join(lines)


async def generate_response(
    session: HoneypotSessionState,
    scammer_message: str,
    strategy: EngagementStrategy
) -> str:
    """
    Generate a human-like response using the persona engine.
    """
    
    persona = session.persona_context
    
    # Format persona traits
    traits = persona.get("traits", ["confused", "worried"])
    traits_str = ", ".join(traits) if isinstance(traits, list) else str(traits)
    
    # Format conversation history
    history = format_conversation_history(session.messages)
    history = history.replace("{name}", session.persona_name)
    
    prompt = get_persona_prompt().format(
        persona_name=session.persona_name,
        age=persona.get("age", 55),
        occupation=persona.get("occupation", "Retired"),
        location=persona.get("location", "India"),
        tech_comfort=persona.get("tech_comfort", "low"),
        family=persona.get("family", "Lives with family"),
        banking=persona.get("banking", "Uses bank account"),
        traits=traits_str,
        engagement_stage=session.stage.value,
        conversation_history=history,
        info_requested=", ".join(session.information_requested_by_scammer) or "Nothing yet",
        info_shared=", ".join(session.information_seemingly_shared) or "Nothing yet",
        strategy=strategy.value
    )
    
    payload = {
        "system_instruction": prompt,
        "user": {"scammer_says": scammer_message}
    }
    
    try:
        result = await run_gemini(payload)
        
        if "raw_output" in result:
            # LLM might return JSON or plain text
            raw = result["raw_output"]
            try:
                parsed = json.loads(raw)
                return parsed.get("reply", parsed.get("response", raw))
            except json.JSONDecodeError:
                return raw.strip()
        elif "error" in result:
            return generate_fallback_response(session, strategy)
        else:
            # Direct dict response
            return result.get("reply", result.get("response", str(result)))
            
    except Exception:
        return generate_fallback_response(session, strategy)


def generate_fallback_response(
    session: HoneypotSessionState,
    strategy: EngagementStrategy
) -> str:
    """Generate a safe fallback response if LLM fails."""
    
    name = session.persona_name
    
    fallbacks = {
        EngagementStrategy.ASK_CLARIFICATION: [
            f"Hello? Wait, I don't understand... what is happening with my account?",
            f"But sir, why do you need this? Can you explain again?",
            f"What? I am confused... what should I do exactly?",
        ],
        EngagementStrategy.PRETEND_CONFUSION: [
            f"Sorry sorry, I didn't understand that... what do you mean?",
            f"Wait, can you say that again? I'm not understanding...",
            f"Haan? What is this you are saying? I am confused...",
        ],
        EngagementStrategy.DELAY_COMPLIANCE: [
            f"Okay okay, let me find my phone... just give me 2 minutes",
            f"Wait, I need to get my reading glasses first...",
            f"One second, I have to search for my card... where did I keep it...",
        ],
        EngagementStrategy.REQUEST_VERIFICATION: [
            f"But how do I know you are really from the bank? My son told me to be careful...",
            f"Sir, can you tell me which branch you are calling from?",
            f"Wait, but bank never asks for this on phone... are you sure?",
        ],
        EngagementStrategy.CLAIM_PARTIAL_COMPLIANCE: [
            f"But I already did this yesterday? Didn't it work?",
            f"Wait, I shared all this with someone who called last week...",
            f"I thought this was already done? You people called before also...",
        ],
        EngagementStrategy.EXPRESS_WORRY: [
            f"But... is my money safe? I am getting worried now...",
            f"Sir, what will happen to my savings? I am very tensed...",
            f"Please tell me my account is okay... I worked so hard for that money...",
        ],
        EngagementStrategy.TECHNICAL_DIFFICULTY: [
            f"Hello? Hello? I can't hear you properly... network problem...",
            f"Wait, my phone is hanging... let me... hello?",
            f"Sorry, screen froze... what were you saying?",
        ],
    }
    
    import random
    options = fallbacks.get(strategy, fallbacks[EngagementStrategy.PRETEND_CONFUSION])
    return random.choice(options)


def generate_exit_response(session: HoneypotSessionState, reason: str) -> str:
    """Generate a natural exit response."""
    
    exit_responses = [
        "Hello? Hello? I think network is gone... I will call you back...",
        "Wait, someone is at the door... I have to go... call me later please",
        "Okay okay, let me think about this... I need to ask my son first...",
        "My phone battery is very low... it might switch off... I will do this later",
        "Sorry, I have to go to temple now... can we do this tomorrow?",
        "I am feeling unwell suddenly... let me rest and call you back...",
        "My daughter-in-law is calling me for lunch... I have to go...",
        "Wait, I need to check with my bank branch first... I will go tomorrow",
    ]
    
    import random
    return random.choice(exit_responses)


def detect_info_requests(scammer_message: str) -> List[str]:
    """Detect what information the scammer is asking for."""
    
    msg_lower = scammer_message.lower()
    requests = []
    
    patterns = {
        "OTP": ["otp", "one time password", "code", "verification code"],
        "PIN": ["pin", "atm pin", "upi pin"],
        "CVV": ["cvv", "security code", "3 digit"],
        "Card Number": ["card number", "debit card", "credit card", "16 digit"],
        "Account Number": ["account number", "bank account", "a/c number"],
        "Aadhaar": ["aadhaar", "aadhar", "uidai", "12 digit"],
        "PAN": ["pan card", "pan number"],
        "Password": ["password", "net banking password", "login"],
        "UPI PIN": ["upi pin", "payment pin"],
        "Personal Details": ["name", "address", "date of birth", "dob"],
        "Payment": ["send money", "transfer", "pay", "rupees"],
        "App Install": ["install", "download", "anydesk", "teamviewer"],
    }
    
    for info_type, keywords in patterns.items():
        if any(kw in msg_lower for kw in keywords):
            requests.append(info_type)
    
    return requests
