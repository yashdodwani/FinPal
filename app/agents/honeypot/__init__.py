"""
Honeypot Agent Package
----------------------

Agentic honeypot system for scammer engagement and intelligence extraction.

Components:
- session_manager: Manages conversation state
- persona_engine: Generates human-like responses
- intelligence_extractor: Extracts scam intelligence
- callback_reporter: Sends final results
- pipeline: Orchestrates the honeypot flow
"""

from .pipeline import run_honeypot_pipeline, handle_honeypot_message
from .session_manager import SessionManager, get_session_manager

__all__ = [
    "run_honeypot_pipeline",
    "handle_honeypot_message",
    "SessionManager",
    "get_session_manager",
]
