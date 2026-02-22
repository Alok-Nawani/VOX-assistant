from typing import Dict, Any, Optional
from dataclasses import dataclass
from .router import CommandRouter
from .memory import MemoryManager, FactExtractor
from .proactive_engine import ProactiveEngine
import asyncio

@dataclass
class Response:
    """Structured response from the assistant"""
    display_text: str
    speak_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class Orchestrator:
    """Brain of the assistant, powered by CommandRouter"""
    
    def __init__(self):
        self.router = CommandRouter()
        self.memory = MemoryManager()
        self.extractor = FactExtractor(self.memory)
        
        # Initialize Proactive Engine
        self.proactive = ProactiveEngine(self._proactive_callback)
        asyncio.create_task(self.proactive.run())
        
    async def _proactive_callback(self, message: str):
        """Handle messages initiated by Vox spontaneously (Default to first user for now or latest active)"""
        # For simplicity in this demo, we'll log to user 1 if not specified
        self.memory.log_interaction(1, "assistant", message)
        
    async def handle_async(self, text: str, user_id: int = 1, image: Optional[str] = None) -> Response:
        """Process commands through the router asynchronously for a specific user"""
        history = self.memory.get_recent_context(user_id)
        facts = self.memory.get_all_facts(user_id)
        self.memory.log_interaction(user_id, "user", text, image_url=image)
        self.proactive.notify_interaction()
        
        try:
            result = await self.router.route(text, user_id=user_id, history=history, facts=facts, image=image)
            reply_text = result.get("message", "I didn't quite catch that.")
            
            self.memory.log_interaction(user_id, "assistant", reply_text)
            
            # Background fact extraction (Temporarily disabled to save API quota for framing)
            # asyncio.create_task(self.extractor.extract_and_store(user_id, f"User: {text}\nVox: {reply_text}"))
            
            return Response(
                display_text=reply_text,
                data=result.get("data")
            )
        except Exception as e:
            return Response(
                display_text=f"I'm having a bit of trouble with my brain right now: {str(e)}"
            )

    def sign_up(self, username: str, password: str) -> int:
        import bcrypt
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return self.memory.create_user(username, pw_hash)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        import bcrypt
        user = self.memory.get_user(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return {"id": user['id'], "username": user['username']}
        return None

# Global orchestrator instance
_brain = None

async def handle(text: str, user_id: int = 1, image: Optional[str] = None) -> Response:
    """Main entry point used by apps (async version)"""
    global _brain
    if _brain is None:
        _brain = Orchestrator()
    return await _brain.handle_async(text, user_id, image=image)
