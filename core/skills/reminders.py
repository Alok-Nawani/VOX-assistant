from typing import Dict, Any, Optional, List
import re
from datetime import datetime, timedelta
import logging
import parsedatetime
from dateutil import parser as date_parser

from core.memory.database import DatabaseManager, Reminder

class ReminderParser:
    def __init__(self):
        """Initialize date/time parsing tools"""
        self.cal = parsedatetime.Calendar()
        
    def _extract_time(self, text: str) -> Optional[datetime]:
        """Extract time from natural language text"""
        try:
            # Try dateutil parser first
            return date_parser.parse(text, fuzzy=True)
        except:
            # Fall back to parsedatetime
            time_struct, parse_status = self.cal.parse(text)
            if parse_status > 0:
                return datetime(*time_struct[:6])
        return None
        
    def parse_reminder(self, text: str) -> Dict[str, Any]:
        """Parse reminder text into structured data"""
        text = text.lower()
        
        # Time patterns
        time_patterns = [
            r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',  # at 3pm, at 15:30
            r'on\s+([a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?)',  # on March 15th
            r'in\s+(\d+)\s*(minute|hour|day)s?',  # in 5 minutes, in 1 hour
            r'tomorrow\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',  # tomorrow at 2pm
            r'next\s+([a-zA-Z]+)',  # next Monday, next week
        ]
        
        # Extract time information
        time_text = None
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                time_text = match.group(0)
                text = text.replace(time_text, '').strip()
                break
                
        # Parse the time
        if time_text:
            due_at = self._extract_time(time_text)
        else:
            # Default to tomorrow morning if no time specified
            due_at = datetime.now().replace(hour=9, minute=0) + timedelta(days=1)
            
        # Set reminder 15 minutes before due time by default
        remind_at = due_at - timedelta(minutes=15) if due_at else None
        
        # Clean up the reminder text
        title = text.replace('remind me to', '').replace('remind me', '').strip()
        
        return {
            "title": title,
            "due_at": due_at,
            "remind_at": remind_at
        }

class ReminderSkill:
    def __init__(self):
        """Initialize the reminder skill"""
        self.db = DatabaseManager()
        self.parser = ReminderParser()
        
    def create_reminder(self, text: str) -> Dict[str, Any]:
        """Create a new reminder from natural language input"""
        try:
            # Parse the reminder text
            parsed = self.parser.parse_reminder(text)
            
            # Create reminder object
            reminder = Reminder(
                id=None,
                title=parsed["title"],
                description=None,
                due_at=parsed["due_at"],
                remind_at=parsed["remind_at"]
            )
            
            # Save to database
            reminder_id = self.db.add_reminder(reminder)
            
            if not reminder_id:
                return {
                    "ok": False,
                    "summary": "Failed to create reminder"
                }
                
            # Format success message
            due_str = reminder.due_at.strftime("%I:%M %p on %B %d")
            return {
                "ok": True,
                "summary": f"I'll remind you to {reminder.title} at {due_str}",
                "data": {"reminder_id": reminder_id}
            }
            
        except Exception as e:
            logging.error(f"Error creating reminder: {e}")
            return {
                "ok": False,
                "summary": f"Sorry, I couldn't create that reminder: {str(e)}"
            }
            
    def list_reminders(self) -> Dict[str, Any]:
        """List pending reminders"""
        try:
            reminders = self.db.get_pending_reminders(limit=5)
            
            if not reminders:
                return {
                    "ok": True,
                    "summary": "You have no pending reminders."
                }
                
            # Format reminder list
            reminder_texts = []
            for r in reminders:
                due_str = r.due_at.strftime("%I:%M %p on %B %d")
                reminder_texts.append(f"- {r.title} (due {due_str})")
                
            summary = "Here are your pending reminders:\n" + "\n".join(reminder_texts)
            
            return {
                "ok": True,
                "summary": summary,
                "data": {"reminders": reminders}
            }
            
        except Exception as e:
            logging.error(f"Error listing reminders: {e}")
            return {
                "ok": False,
                "summary": f"Sorry, I couldn't get your reminders: {str(e)}"
            }
            
    def complete_reminder(self, reminder_id: int) -> Dict[str, Any]:
        """Mark a reminder as completed"""
        try:
            success = self.db.mark_reminder_complete(reminder_id)
            
            if success:
                return {
                    "ok": True,
                    "summary": "Reminder marked as completed"
                }
            else:
                return {
                    "ok": False,
                    "summary": "Reminder not found"
                }
                
        except Exception as e:
            logging.error(f"Error completing reminder: {e}")
            return {
                "ok": False,
                "summary": f"Sorry, I couldn't complete that reminder: {str(e)}"
            }
            
    def delete_reminder(self, reminder_id: int) -> Dict[str, Any]:
        """Delete a reminder"""
        try:
            success = self.db.delete_reminder(reminder_id)
            
            if success:
                return {
                    "ok": True,
                    "summary": "Reminder deleted"
                }
            else:
                return {
                    "ok": False,
                    "summary": "Reminder not found"
                }
                
        except Exception as e:
            logging.error(f"Error deleting reminder: {e}")
            return {
                "ok": False,
                "summary": f"Sorry, I couldn't delete that reminder: {str(e)}"
            }

# Skill entrypoint
def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Run the reminder skill"""
    skill = ReminderSkill()
    action = payload.get("action", "")
    
    if action == "create_reminder":
        return skill.create_reminder(payload["text"])
    elif action == "list_reminders":
        return skill.list_reminders()
    elif action == "complete_reminder":
        return skill.complete_reminder(payload["reminder_id"])
    elif action == "delete_reminder":
        return skill.delete_reminder(payload["reminder_id"])
    else:
        return {
            "ok": False,
            "summary": f"Unknown action: {action}"
        }
