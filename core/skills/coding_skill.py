from .base_skill import BaseSkill
from typing import Dict, Any
import logging

class CodingSkill(BaseSkill):
    """Skill for generating and explaining code solutions"""
    
    def __init__(self):
        super().__init__("coding")
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "")
        language = params.get("language", "en")
        
        # Use conversation handler but with a coding-specific prompt
        from ..ai.conversation import AIConversationHandler
        handler = AIConversationHandler()
        
        coding_prompt = (
            f"Alok has requested a technical/coding solution: '{text}'.\n"
            "Provide high-quality, efficient code. "
            "Use Markdown formatting with language tags (e.g., ```python). "
            "Explain the logic briefly as a 'System Architect'. "
            f"Respond in {language}."
        )
        
        message = await handler.get_response(coding_prompt, params.get("history"), params.get("facts"))
        
        return {
            "success": True,
            "message": message,
            "data": {
                "type": "code_solution",
                "content": message
            }
        }
