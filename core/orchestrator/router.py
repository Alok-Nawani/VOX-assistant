from typing import Dict, Any
from ..skills.system_control import SystemControlSkill
from ..skills.weather_skill import WeatherSkill
from ..skills.conversation_skill import ConversationSkill
from ..skills.whatsapp_skill import WhatsAppSkill
from ..skills.file_management_skill import FileManagementSkill
from ..skills.calendar_skill import CalendarSkill
from ..skills.email_skill import EmailSkill
from ..skills.media_control_skill import MediaControlSkill
from ..skills.news_skill import NewsSkill

class CommandRouter:
    """Central command router for Vox Assistant"""
    
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
        }
        self.default_skill = "conversation"
        self.active_skill: Optional[str] = None
        
    async def route(self, text: str, user_id: int = 1, history: list = None, facts: dict = None, image: str = None) -> Dict[str, Any]:
        """Route a command to the appropriate skill for a specific user"""
        text = text.lower().strip()
        
        # Unified Params Bag
        params = {
            "user_id": user_id,
            "raw_text": text,
            "history": history,
            "facts": facts,
            "image": image,
            "is_followup": False
        }
        
        # 0. Check for active multi-turn session
        if self.active_skill and self.active_skill in self.skills:
            params["is_followup"] = True
            result = await self.skills[self.active_skill].execute(params)
            if not result.get("keep_active", False):
                self.active_skill = None
            return result

        # 1. Direct Intent Mapping
        intent = self._detect_intent(text)
        
        # 2. Get the skill
        skill_name = self._get_skill_for_intent(intent, text)
        
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            params["intent"] = intent
            params["entities"] = {} # For future expansion
            try:
                result = await skill.execute(params)
                if result.get("keep_active"):
                    self.active_skill = skill_name
                return result
            except Exception as e:
                import logging
                logging.error(f"Error executing skill {skill_name}: {e}")
                return {"success": False, "message": f"Something went wrong with the {skill_name} skill."}
        
        # 3. Fallback to conversation (LLM)
        return await self._handle_conversation(text, image=image)

    def _detect_intent(self, text: str) -> str:
        words = text.split()
        
        # 1. Communication (Check this before generic 'open' commands)
        if any(cmd in text for cmd in ["whatsapp", "message", "text"]):
            return "send_message"
        if any(cmd in text for cmd in ["email", "inbox", "mailbox", "mail", "gmail"]):
            return "email"
            
        # 2. System Control
        system_cmds = ["open ", "launch ", "screenshot", "sleep", "lock", "battery", "stats", "cpu", "ram", "click", "picture", "photo", "camera", "capture"]
        if any(cmd in text for cmd in system_cmds):
             return "system_control"
        if any(word in words for word in ["open", "close", "quit", "volume", "dim", "brightness", "screen"]):
             return "system_control"
              
        # 3. Weather
        if "weather" in words or "weather" in text:
            return "get_weather"
            
        # 4. Media
        media_cmds = ["pause", "skip", "next song", "previous track", "stop music", "resume"]
        if any(cmd in text for cmd in media_cmds):
            return "media"
        if "play" in words or ("play" in text and "display" not in text):
            return "media"

        # 5. Other specialized skills
        if any(cmd in text for cmd in ["file", "search", "find", "list", "directory", "folder"]):
            return "file_ops"
        if any(cmd in text for cmd in ["calendar", "event", "meeting", "schedule"]):
            return "calendar"
        
        if any(cmd in text for cmd in ["news", "headline", "happening"]):
            return "news"
        
        # Hard-wired camera bypass
        if any(cmd in text for cmd in ["picture", "photo", "camera", "capture"]):
            return "system_control"
            
        return "conversation"

    def _get_skill_for_intent(self, intent: str, text: str) -> str:
        if intent == "system_control":
            return "system_control"
        if intent == "get_weather":
            return "weather"
        if intent == "send_message":
            return "whatsapp"
        if intent == "file_ops":
            return "file_ops"
        if intent == "calendar":
            return "calendar"
        if intent == "email":
            return "email"
        if intent == "media":
            return "media"
        if intent == "news":
            return "news"
        return "conversation"

    async def _handle_conversation(self, text: str, image: str = None) -> Dict[str, Any]:
        """Use the conversation skill for general queries"""
        skill = self.skills.get("conversation")
        if skill:
            return await skill.execute({"raw_text": text, "image": image})
        return {"success": False, "message": "Conversational AI is not available."}
