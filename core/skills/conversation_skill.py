from ..skills.base_skill import BaseSkill
from ..ai.conversation import AIConversationHandler
from typing import Dict, Any

class ConversationSkill(BaseSkill):
    """Skill for handling general natural language conversations"""
    
    def __init__(self):
        super().__init__("conversation")
        self.handler = AIConversationHandler()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "")
        
        # Check for specific intents
        if "movie" in text.lower() or "watch" in text.lower():
            message = self.handler.get_movie_recommendation()
        else:
            history = params.get("history", [])
            facts = params.get("facts", {})
            image = params.get("image")
            language = params.get("language", "en")
            tone = params.get("tone", "Jarvis")
            message = await self.handler.get_response(text, history, facts, image=image, language=language, tone=tone)
            
        return {
            "success": True,
            "message": message
        }
