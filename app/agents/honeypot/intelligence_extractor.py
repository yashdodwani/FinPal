"""
Intelligence Extractor
----------------------

Extracts scam intelligence from scammer messages.
Uses both regex patterns (fast) and LLM (comprehensive).
"""

import re
import json
from typing import List, Dict, Any

from app.schemas.honeypot import ExtractedIntelligence, ConversationMessage
from app.core.gemini import run_gemini
from .prompts import get_extraction_prompt


# Regex patterns for fast extraction
PATTERNS = {
    "upi_id": re.compile(
        r'[a-zA-Z0-9._-]+@(?:ybl|paytm|okicici|okaxis|okhdfcbank|oksbi|apl|axisbank|'
        r'ibl|sbi|icici|hdfcbank|axisb|upi|freecharge|amazonpay|gpay|phonepe|'
        r'airtel|postbank|kotak|indus|rbl|federal|idbi|pnb|boi|bob|cbi)',
        re.IGNORECASE
    ),
    "phone_number": re.compile(
        r'(?:\+91[\s-]?)?(?:0)?[6-9]\d{9}\b'
    ),
    "bank_account": re.compile(
        r'\b\d{9,18}\b'  # Bank accounts are typically 9-18 digits
    ),
    "url": re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+|'
        r'(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly|is\.gd|buff\.ly|'
        r'adf\.ly|bit\.do|mcaf\.ee)/[a-zA-Z0-9]+',
        re.IGNORECASE
    ),
    "email": re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    ),
}

# Keywords indicating scam tactics
SCAM_KEYWORDS = {
    "urgency": [
        "immediately", "urgent", "right now", "within 1 hour", "today only",
        "expires", "last chance", "hurry", "quick", "asap", "deadline",
        "account will be blocked", "suspended", "deactivated"
    ],
    "authority": [
        "rbi", "reserve bank", "police", "cbi", "cyber cell", "court",
        "government", "income tax", "ed", "enforcement", "legal department",
        "compliance", "regulatory"
    ],
    "fear": [
        "arrest", "legal action", "fir", "case filed", "money laundering",
        "penalty", "fine", "jail", "criminal", "investigation", "seized"
    ],
    "greed": [
        "lottery", "prize", "winner", "cashback", "refund", "bonus",
        "reward", "lucky", "congratulations", "selected", "free"
    ],
    "data_request": [
        "otp", "pin", "cvv", "password", "card number", "account number",
        "aadhaar", "pan", "bank details", "verify", "confirm identity"
    ],
    "remote_access": [
        "anydesk", "teamviewer", "quick support", "remote", "screen share",
        "install app", "download", "allow access"
    ]
}


def extract_with_regex(text: str) -> ExtractedIntelligence:
    """Fast regex-based extraction."""
    
    text_lower = text.lower()
    
    # Extract structured data
    upi_ids = PATTERNS["upi_id"].findall(text)
    phone_numbers = PATTERNS["phone_number"].findall(text)
    urls = PATTERNS["url"].findall(text)
    emails = PATTERNS["email"].findall(text)
    
    # Bank accounts - filter out likely non-accounts (dates, prices, etc.)
    potential_accounts = PATTERNS["bank_account"].findall(text)
    bank_accounts = [
        acc for acc in potential_accounts 
        if len(acc) >= 10 and not acc.startswith('0')
    ]
    
    # Extract scam keywords
    found_keywords = []
    for category, keywords in SCAM_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found_keywords.append(f"{category}:{kw}")
    
    # Detect app names
    app_names = []
    remote_apps = ["anydesk", "teamviewer", "quick support", "ammyy", "ultraviewer"]
    for app in remote_apps:
        if app in text_lower:
            app_names.append(app.title())
    
    # Detect payment requests (basic)
    payment_requests = []
    amount_pattern = re.compile(r'(?:rs\.?|₹|inr)\s*(\d+(?:,\d+)*(?:\.\d{2})?)', re.IGNORECASE)
    amounts = amount_pattern.findall(text)
    if amounts:
        for amt in amounts:
            payment_requests.append({
                "amount": amt.replace(",", ""),
                "purpose": "unknown",
                "raw_text": text[:100]
            })
    
    return ExtractedIntelligence(
        bank_accounts=list(set(bank_accounts)),
        upi_ids=list(set(upi_ids)),
        phishing_urls=list(set(urls)),
        phone_numbers=list(set(phone_numbers)),
        email_addresses=list(set(emails)),
        scam_keywords=list(set(found_keywords)),
        app_names=list(set(app_names)),
        payment_requests=payment_requests
    )


async def extract_with_llm(
    scammer_message: str,
    conversation_history: List[ConversationMessage]
) -> ExtractedIntelligence:
    """LLM-based extraction for comprehensive analysis."""
    
    # Format conversation history
    history_text = "\n".join([
        f"{msg.role.upper()}: {msg.content}"
        for msg in conversation_history[-10:]  # Last 10 messages
    ])
    
    prompt = get_extraction_prompt().format(
        scammer_message=scammer_message,
        conversation_history=history_text or "No previous messages."
    )
    
    payload = {
        "system_instruction": prompt,
        "user": {"message": scammer_message}
    }
    
    try:
        result = await run_gemini(payload)
        
        # Parse the result
        if "raw_output" in result:
            parsed = json.loads(result["raw_output"])
        elif "error" in result:
            return ExtractedIntelligence()
        else:
            parsed = result
        
        return ExtractedIntelligence(
            bank_accounts=parsed.get("bank_accounts", []),
            upi_ids=parsed.get("upi_ids", []),
            phishing_urls=parsed.get("phishing_urls", []),
            phone_numbers=parsed.get("phone_numbers", []),
            email_addresses=parsed.get("email_addresses", []),
            scam_keywords=parsed.get("scam_keywords", []),
            app_names=parsed.get("app_names", []),
            payment_requests=parsed.get("payment_requests", [])
        )
        
    except Exception:
        return ExtractedIntelligence()


async def extract_intelligence(
    scammer_message: str,
    conversation_history: List[ConversationMessage],
    use_llm: bool = True
) -> ExtractedIntelligence:
    """
    Main extraction function.
    Combines regex (fast) and optional LLM (comprehensive) extraction.
    """
    
    # Always do regex extraction (fast)
    regex_result = extract_with_regex(scammer_message)
    
    if not use_llm:
        return regex_result
    
    # Do LLM extraction for comprehensive analysis
    llm_result = await extract_with_llm(scammer_message, conversation_history)
    
    # Merge results
    return ExtractedIntelligence(
        bank_accounts=list(set(regex_result.bank_accounts + llm_result.bank_accounts)),
        upi_ids=list(set(regex_result.upi_ids + llm_result.upi_ids)),
        phishing_urls=list(set(regex_result.phishing_urls + llm_result.phishing_urls)),
        phone_numbers=list(set(regex_result.phone_numbers + llm_result.phone_numbers)),
        email_addresses=list(set(regex_result.email_addresses + llm_result.email_addresses)),
        scam_keywords=list(set(regex_result.scam_keywords + llm_result.scam_keywords)),
        app_names=list(set(regex_result.app_names + llm_result.app_names)),
        payment_requests=regex_result.payment_requests + llm_result.payment_requests
    )


def has_valuable_intelligence(intel: ExtractedIntelligence) -> bool:
    """Check if we've extracted valuable intelligence."""
    
    return bool(
        intel.bank_accounts or
        intel.upi_ids or
        intel.phishing_urls or
        intel.phone_numbers or
        intel.email_addresses or
        intel.app_names
    )


def summarize_intelligence(intel: ExtractedIntelligence) -> str:
    """Create a brief summary of extracted intelligence."""
    
    parts = []
    
    if intel.upi_ids:
        parts.append(f"UPI: {', '.join(intel.upi_ids[:3])}")
    if intel.bank_accounts:
        parts.append(f"Accounts: {len(intel.bank_accounts)}")
    if intel.phishing_urls:
        parts.append(f"URLs: {len(intel.phishing_urls)}")
    if intel.phone_numbers:
        parts.append(f"Phones: {', '.join(intel.phone_numbers[:2])}")
    if intel.app_names:
        parts.append(f"Apps: {', '.join(intel.app_names)}")
    if intel.scam_keywords:
        keywords = [k.split(':')[1] for k in intel.scam_keywords[:5]]
        parts.append(f"Keywords: {', '.join(keywords)}")
    
    return " | ".join(parts) if parts else "No intelligence yet"
