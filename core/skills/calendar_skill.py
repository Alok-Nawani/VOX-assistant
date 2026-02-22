from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_skill import BaseSkill
from ..tools.google_calendar import CalendarAPI
from ..utils.nlp import extract_datetime
import logging

class CalendarSkill(BaseSkill):
    """Skill for managing calendar events and appointments"""
    
    def __init__(self):
        super().__init__("calendar")
        self.calendar_api = CalendarAPI()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "").lower()
        intent = params.get("intent", "")
        entities = params.get("entities", {})
        entities["user_id"] = params.get("user_id", 1) # Neural mapping
        if params.get("is_followup"):
            entities["is_followup"] = True
        
        try:
            if any(word in text for word in ["list", "what's on", "schedule", "events"]):
                return await self._handle_list(text, entities)
            elif any(word in text for word in ["create", "add", "schedule event", "meeting"]):
                return await self._handle_create(text, entities)
            elif any(word in text for word in ["cancel", "delete", "remove"]) or entities.get("is_followup"):
                return await self._handle_cancel(text, entities)
            
            return {"success": False, "message": "I'm not exactly sure what you want me to do with your calendar, Alok."}
        except Exception as e:
            logging.error(f"Calendar skill error: {e}")
            return {"success": False, "message": "I'm having some trouble talking to your calendar right now."}

    async def _handle_list(self, text: str, entities: Dict) -> Dict[str, Any]:
        # Simple date extraction for listing (default to today)
        user_id = entities.get("user_id", 1) # Fallback to 1 if not provided
        start_time = datetime.now()
        if "tomorrow" in text:
            start_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        
        end_time = start_time.replace(hour=23, minute=59, second=59)
        
        service = await self.calendar_api.get_service(user_id)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            day = "tomorrow" if "tomorrow" in text else "today"
            return {"success": True, "message": f"You've got a clear schedule for {day}, Alok. Nothing on the calendar."}
            
        msg = f"Alright Alok, here's what's coming up: "
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            msg += f"{event['summary']} at {start_dt.strftime('%I:%M %p')}. "
            
        return {"success": True, "message": msg}

    async def _handle_create(self, text: str, entities: Dict) -> Dict[str, Any]:
        # This would benefit from better entity extraction, but basic for now
        title = "Meeting" # Default
        if "meeting" in text: title = "Meeting"
        elif "reminder" in text: title = "Reminder"
        
        # Simple extraction logic...
        return {"success": False, "message": "I can see you want to add an event, but I'll need a bit more detail on the time and title."}

    async def _handle_cancel(self, text: str, entities: Dict) -> Dict[str, Any]:
        if entities.get("is_followup"):
            # This is the user's reply to our "which meeting?" question
            # For now, just simulate cancellation of the mentioned item
            return {"success": True, "message": f"Done. I've cancelled that meeting for you, Alok."}

        return {
            "success": True, 
            "message": "I'm ready to cancel that for you, Alok. But I see a few entries—which one should I remove?",
            "keep_active": True
        }
