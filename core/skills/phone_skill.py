from typing import Dict, Optional
from .base_skill import BaseSkill
from ..tools.phone_controller import PhoneController
import logging

class PhoneSkill(BaseSkill):
    """Skill for phone control"""
    
    def __init__(self):
        super().__init__()
        self.name = "phone"
        self.controller = PhoneController()
        self.initialized = False
        
    async def initialize(self):
        """Initialize phone integration"""
        if self.initialized:
            return
            
        await self.controller.initialize()
        self.initialized = True
        
    async def handle_intent(self, intent: str, entities: Dict) -> str:
        """Handle phone-related intents"""
        try:
            if not self.initialized:
                await self.initialize()
                
            if intent == "send_message":
                return await self.send_message(entities)
            elif intent == "read_messages":
                return await self.read_messages(entities)
            elif intent == "make_call":
                return await self.make_call(entities)
            elif intent == "check_calls":
                return await self.check_calls(entities)
            else:
                return "I'm not sure how to handle that phone request."
        except Exception as e:
            logging.error(f"Error in phone skill: {e}")
            return "Sorry, I encountered an error while managing phone functions."
            
    async def send_message(self, entities: Dict) -> str:
        """Send an SMS message"""
        try:
            recipient = entities.get("recipient")
            message = entities.get("message")
            
            if not all([recipient, message]):
                return "I need both a recipient and message to send an SMS."
                
            success = await self.controller.send_sms(recipient, message)
            
            if success:
                return f"Message sent to {recipient}"
            else:
                return f"Failed to send message to {recipient}"
                
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return "Sorry, I couldn't send the message."
            
    async def read_messages(self, entities: Dict) -> str:
        """Read recent messages"""
        try:
            limit = entities.get("limit", 5)
            messages = await self.controller.get_messages(limit)
            
            if not messages:
                return "No recent messages found."
                
            response = "Here are your recent messages:\n\n"
            for message in messages:
                response += self.controller.format_message(message)
                
            return response
            
        except Exception as e:
            logging.error(f"Error reading messages: {e}")
            return "Sorry, I couldn't read your messages."
            
    async def make_call(self, entities: Dict) -> str:
        """Make a phone call"""
        try:
            recipient = entities.get("recipient")
            if not recipient:
                return "Who would you like to call?"
                
            success = await self.controller.make_call(recipient)
            
            if success:
                return f"Calling {recipient}"
            else:
                return f"Failed to call {recipient}"
                
        except Exception as e:
            logging.error(f"Error making call: {e}")
            return "Sorry, I couldn't make the call."
            
    async def check_calls(self, entities: Dict) -> str:
        """Check call history"""
        try:
            limit = entities.get("limit", 5)
            calls = await self.controller.get_call_history(limit)
            
            if not calls:
                return "No recent calls found."
                
            response = "Here's your recent call history:\n\n"
            for call in calls:
                response += self.controller.format_call(call)
                
            return response
            
        except Exception as e:
            logging.error(f"Error checking calls: {e}")
            return "Sorry, I couldn't check your call history."
