from typing import Dict, Any, Optional
import logging
from ..skills.system_control import SystemControlSkill
from ..skills.weather_skill import WeatherSkill
from ..skills.conversation_skill import ConversationSkill
from ..skills.whatsapp_skill import WhatsAppSkill
from ..skills.file_management_skill import FileManagementSkill
from ..skills.calendar_skill import CalendarSkill
from ..skills.email_skill import EmailSkill
from ..skills.media_control_skill import MediaControlSkill
from ..skills.news_skill import NewsSkill
from ..skills.vision_skill import VisionSkill
from ..skills.coding_skill import CodingSkill
from ..skills.art_skill import ArtSkill
from ..ai.intent_parser import IntentParser

class CommandRouter:
    """Central command router for Vox Assistant powered by AI Intent Parsing"""
    
    def __init__(self):
        self.skills = {
            "system_control": SystemControlSkill(),
            "conversation": ConversationSkill(),
            "weather": WeatherSkill(),
            "whatsapp": WhatsAppSkill(),
            "file_ops": FileManagementSkill(),
            "calendar": CalendarSkill(),
            "email": EmailSkill(),
            "media": MediaControlSkill(),
            "news": NewsSkill(),
            "vision": VisionSkill(),
            "coding": CodingSkill(),
            "art": ArtSkill(),
        }
        self.active_skill: Optional[str] = None
        self.intent_parser = IntentParser()
        
    async def route(self, text: str, user_id: int = 1, history: list = None, facts: dict = None, image: str = None, language: str = "en", tone: str = "Jarvis") -> Dict[str, Any]:
        """Route a command to the appropriate skill for a specific user"""
        text = text.lower().strip()
        
        # Unified Params Bag
        params = {
            "user_id": user_id,
            "raw_text": text,
            "history": history,
            "facts": facts,
            "image": image,
            "language": language,
            "tone": tone,
            "is_followup": False
        }
        
        # 0. Check for active multi-turn session
        reset_keywords = ["hi", "hello", "cancel", "stop", "reset", "hey vox", "yo"]
        if self.active_skill and self.active_skill in self.skills:
            if text in reset_keywords:
                logging.info(f"Session reset triggered by keyword: {text}")
                self.active_skill = None
                # Fall through to normal routing
            else:
                params["is_followup"] = True
                result = await self.skills[self.active_skill].execute(params)
                if not result.get("keep_active", False):
                    self.active_skill = None
                return result

        # 1. Parse Intents using Gemini Flash
        aliases = {k.replace('alias_', ''): v for k, v in facts.items() if k.startswith('alias_')} if facts else {}
        steps = await self.intent_parser.parse(text, aliases)
        
        results = []
        combined_data = {}
        
        # 2. Execute each step sequentially
        for step in steps:
            skill_name = step.get("skill", "conversation")
            query = step.get("query", text)
            
            if skill_name in self.skills:
                skill = self.skills[skill_name]
                params["raw_text"] = text # Keep original text for keyword matching
                params["query"] = query    # Pass parsed query for specific extraction
                params["intent"] = skill_name
                
                try:
                    res = await skill.execute(params)
                    if res.get("message"):
                        results.append(res["message"])
                    if res.get("data"):
                        combined_data.update(res["data"])
                    if res.get("keep_active"):
                        self.active_skill = skill_name
                except Exception as e:
                    logging.error(f"Error executing skill {skill_name}: {e}")
                    results.append(f"Something went wrong with {skill_name}.")
            elif skill_name == "learn_command":
                res = await self._handle_learn_command(query)
                results.append(res["message"])
                if res.get("data"):
                    combined_data.update(res["data"])
            else:
                # Fallback to conversation
                params["raw_text"] = query
                res = await self._handle_conversation(params)
                if res.get("message"):
                    results.append(res["message"])
                
        # 3. Aggregate results
        final_message = " ".join(results) if results else "Task completed."
        return {"success": True, "message": final_message, "data": combined_data}

    async def _handle_learn_command(self, query: str) -> Dict[str, Any]:
        """Pass the learn request to brain.py via data signal"""
        return {
            "success": True,
            "message": "I'm analyzing this new command.",
            "data": {
                "learn_request": query
            }
        }

    async def _handle_conversation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Use the conversation skill for general queries"""
        skill = self.skills.get("conversation")
        if skill:
            return await skill.execute(params)
        return {"success": False, "message": "Conversational AI is not available."}
