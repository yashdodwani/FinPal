"""
Session State Manager
---------------------

Manages honeypot conversation state across multiple turns.
Uses in-memory storage with optional database persistence.

Thread-safe singleton pattern for concurrent access.
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
import random

from app.schemas.honeypot import (
    HoneypotSessionState,
    EngagementStage,
    ExtractedIntelligence,
    ConversationMessage,
)


class SessionManager:
    """
    Manages honeypot session state.
    
    In production, this would persist to database.
    For hackathon, uses in-memory dict with lock.
    """
    
    _instance: Optional["SessionManager"] = None
    _sessions: Dict[str, HoneypotSessionState]
    _lock: Optional[asyncio.Lock]
    _initialized: bool
    
    def __new__(cls) -> "SessionManager":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._sessions = {}
            instance._lock = None
            instance._initialized = False
            cls._instance = instance
        return cls._instance
    
    async def _ensure_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    def _generate_persona(self) -> tuple[str, Dict[str, Any]]:
        """Generate a realistic Indian persona for the honeypot."""
        
        personas = [
            {
                "name": "Priya",
                "age": 58,
                "occupation": "Retired school teacher",
                "location": "Pune",
                "tech_comfort": "low",
                "family": "Lives with son and daughter-in-law",
                "banking": "Has SBI account, uses PhonePe sometimes",
                "traits": ["trusting", "anxious about money", "asks family for tech help"]
            },
            {
                "name": "Ramesh",
                "age": 62,
                "occupation": "Retired clerk",
                "location": "Lucknow", 
                "tech_comfort": "very low",
                "family": "Wife, two children in different cities",
                "banking": "Uses PNB, recently started UPI",
                "traits": ["cautious but gullible", "worries about pension", "hard of hearing"]
            },
            {
                "name": "Sunita",
                "age": 45,
                "occupation": "Housewife",
                "location": "Jaipur",
                "tech_comfort": "medium",
                "family": "Husband works abroad, two kids in school",
                "banking": "HDFC account, uses Google Pay",
                "traits": ["worried about family money", "trusts authority figures", "busy with household"]
            },
            {
                "name": "Arun",
                "age": 67,
                "occupation": "Retired government officer",
                "location": "Chennai",
                "tech_comfort": "low",
                "family": "Wife passed away, daughter in Bangalore",
                "banking": "Indian Bank, pension account",
                "traits": ["lonely", "respects authority", "takes time to understand"]
            },
            {
                "name": "Kavita",
                "age": 52,
                "occupation": "Small shop owner",
                "location": "Ahmedabad",
                "tech_comfort": "medium-low",
                "family": "Husband and mother-in-law",
                "banking": "Bank of Baroda, uses Paytm for shop",
                "traits": ["busy", "worried about shop finances", "sometimes confused by banking terms"]
            }
        ]
        
        persona = random.choice(personas)
        return persona["name"], persona
    
    async def get_or_create_session(self, session_id: str) -> HoneypotSessionState:
        """Get existing session or create new one."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.updated_at = datetime.utcnow()
                return session
            
            # Create new session with random persona
            name, context = self._generate_persona()
            
            session = HoneypotSessionState(
                session_id=session_id,
                stage=EngagementStage.INIT,
                persona_name=name,
                persona_context=context,
            )
            
            self._sessions[session_id] = session
            return session
    
    async def get_session(self, session_id: str) -> Optional[HoneypotSessionState]:
        """Get session if exists, None otherwise."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            return self._sessions.get(session_id)
    
    async def update_session(self, session: HoneypotSessionState) -> None:
        """Update session state."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session.updated_at = datetime.utcnow()
            self._sessions[session.session_id] = session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        extracted: Optional[ExtractedIntelligence] = None
    ) -> HoneypotSessionState:
        """Add a message to session history."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            message = ConversationMessage(
                role=role,
                content=content,
                extracted_this_turn=extracted
            )
            session.messages.append(message)
            session.updated_at = datetime.utcnow()
            
            return session
    
    async def accumulate_intelligence(
        self,
        session_id: str,
        new_intel: ExtractedIntelligence
    ) -> ExtractedIntelligence:
        """Merge new intelligence into accumulated intelligence."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            acc = session.accumulated_intelligence
            
            # Merge lists, avoiding duplicates
            acc.bank_accounts = list(set(acc.bank_accounts + new_intel.bank_accounts))
            acc.upi_ids = list(set(acc.upi_ids + new_intel.upi_ids))
            acc.phishing_urls = list(set(acc.phishing_urls + new_intel.phishing_urls))
            acc.phone_numbers = list(set(acc.phone_numbers + new_intel.phone_numbers))
            acc.scam_keywords = list(set(acc.scam_keywords + new_intel.scam_keywords))
            acc.email_addresses = list(set(acc.email_addresses + new_intel.email_addresses))
            acc.app_names = list(set(acc.app_names + new_intel.app_names))
            
            # Append payment requests (may have duplicates, that's ok)
            acc.payment_requests.extend(new_intel.payment_requests)
            
            session.updated_at = datetime.utcnow()
            
            return acc
    
    async def update_stage(
        self,
        session_id: str,
        new_stage: EngagementStage
    ) -> None:
        """Update engagement stage."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if session:
                session.stage = new_stage
                session.updated_at = datetime.utcnow()
    
    async def mark_callback_sent(self, session_id: str) -> None:
        """Mark that callback has been sent for this session."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if session:
                session.callback_sent = True
                session.updated_at = datetime.utcnow()
    
    async def increment_stagnant_turns(self, session_id: str) -> int:
        """Increment turns without progress, return new count."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if session:
                session.turns_without_progress += 1
                session.updated_at = datetime.utcnow()
                return session.turns_without_progress
            return 0
    
    async def reset_stagnant_turns(self, session_id: str) -> None:
        """Reset stagnant turn counter."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            if session:
                session.turns_without_progress = 0
                session.updated_at = datetime.utcnow()
    
    async def get_message_count(self, session_id: str) -> int:
        """Get total messages exchanged."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            session = self._sessions.get(session_id)
            return len(session.messages) if session else 0
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        
        lock = await self._ensure_lock()
        
        async with lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
