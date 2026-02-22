from typing import Dict, Optional
from .base_skill import BaseSkill
from ..tools.security_controller import SecurityController, SecurityEvent
import logging
from datetime import datetime

class SecuritySkill(BaseSkill):
    """Skill for security system control"""
    
    def __init__(self):
        super().__init__()
        self.name = "security"
        self.controller = SecurityController()
        self.initialized = False
        
    async def initialize(self):
        """Initialize security system connection"""
        if self.initialized:
            return
            
        await self.controller.initialize()
        self.controller.add_event_listener(self._handle_security_event)
        self.initialized = True
        
    async def handle_intent(self, intent: str, entities: Dict) -> str:
        """Handle security-related intents"""
        try:
            if not self.initialized:
                await self.initialize()
                
            if intent == "arm_system":
                return await self.arm_system(entities)
            elif intent == "disarm_system":
                return await self.disarm_system(entities)
            elif intent == "get_security_status":
                return await self.get_security_status()
            elif intent == "get_security_events":
                return await self.get_security_events(entities)
            elif intent == "trigger_panic":
                return await self.trigger_panic(entities)
            else:
                return "I'm not sure how to handle that security request."
        except Exception as e:
            logging.error(f"Error in security skill: {e}")
            return "Sorry, I encountered an error while managing the security system."
            
    async def _handle_security_event(self, event: SecurityEvent):
        """Handle incoming security events"""
        # This method will be called by the controller when events occur
        # Implement specific handling logic here
        logging.info(f"Security event received: {event.type} in {event.location}")
        
    async def arm_system(self, entities: Dict) -> str:
        """Arm the security system"""
        try:
            mode = entities.get("mode", "away").lower()
            if mode not in ["away", "stay", "night"]:
                return f"Invalid arming mode: {mode}"
                
            success = await self.controller.arm_system(mode)
            
            if success:
                return f"Security system armed in {mode} mode"
            else:
                return "Failed to arm the security system"
                
        except Exception as e:
            logging.error(f"Error arming system: {e}")
            return "Sorry, I couldn't arm the security system."
            
    async def disarm_system(self, entities: Dict) -> str:
        """Disarm the security system"""
        try:
            code = entities.get("code")
            success = await self.controller.disarm_system(code)
            
            if success:
                return "Security system disarmed"
            else:
                return "Failed to disarm the security system"
                
        except Exception as e:
            logging.error(f"Error disarming system: {e}")
            return "Sorry, I couldn't disarm the security system."
            
    async def get_security_status(self) -> str:
        """Get current security system status"""
        try:
            status = await self.controller.get_system_status()
            
            if not status:
                return "Unable to get security system status"
                
            response = f"Security System Status:\n"
            response += f"Armed: {status['armed']}\n"
            if status['armed']:
                response += f"Mode: {status['mode']}\n"
                
            response += f"All Zones Secure: {status['zones_secure']}\n"
            
            # Add any open zones
            if not status['zones_secure']:
                response += "\nOpen Zones:\n"
                for zone in status['open_zones']:
                    response += f"- {zone['name']}: {zone['status']}\n"
                    
            return response
            
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return "Sorry, I couldn't get the security system status."
            
    async def get_security_events(self, entities: Dict) -> str:
        """Get recent security events"""
        try:
            limit = entities.get("limit", 5)
            events = await self.controller.get_recent_events(limit)
            
            if not events:
                return "No recent security events found"
                
            response = "Recent Security Events:\n\n"
            
            for event in events:
                timestamp = event.timestamp.strftime("%I:%M %p on %B %d")
                response += f"- {event.type.title()} detected in {event.location}\n"
                response += f"  Time: {timestamp}\n"
                response += f"  Status: {event.status}\n"
                if event.details:
                    response += f"  Details: {event.details}\n"
                response += "\n"
                
            return response
            
        except Exception as e:
            logging.error(f"Error getting security events: {e}")
            return "Sorry, I couldn't get the security events."
            
    async def trigger_panic(self, entities: Dict) -> str:
        """Trigger panic alarm"""
        try:
            type = entities.get("type", "police").lower()
            if type not in ["police", "fire", "medical"]:
                return f"Invalid panic type: {type}"
                
            success = await self.controller.trigger_panic(type)
            
            if success:
                return f"Triggered {type} panic alarm"
            else:
                return f"Failed to trigger {type} panic alarm"
                
        except Exception as e:
            logging.error(f"Error triggering panic: {e}")
            return "Sorry, I couldn't trigger the panic alarm."
