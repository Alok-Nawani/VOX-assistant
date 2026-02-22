from typing import Dict, List, Optional
from .base_skill import BaseSkill
from ..tools.automation_controller import AutomationController, Automation
import logging
import json

class AutomationSkill(BaseSkill):
    """Skill for managing automations and routines"""
    
    def __init__(self):
        super().__init__()
        self.name = "automation"
        self.controller = AutomationController()
        self.skill_registry = {}  # Will be populated with available skills
        
    def register_skill(self, skill_name: str, skill_instance: BaseSkill):
        """Register a skill for use in automations"""
        self.skill_registry[skill_name] = skill_instance
        
    async def initialize(self):
        """Initialize automation system"""
        await self.controller.load_automations()
        
    async def handle_intent(self, intent: str, entities: Dict) -> str:
        """Handle automation-related intents"""
        try:
            if intent == "create_routine":
                return await self.create_routine(entities)
            elif intent == "delete_routine":
                return await self.delete_routine(entities)
            elif intent == "list_routines":
                return await self.list_routines()
            elif intent == "toggle_routine":
                return await self.toggle_routine(entities)
            elif intent == "trigger_routine":
                return await self.trigger_routine(entities)
            elif intent == "ifttt_trigger":
                return await self.trigger_ifttt(entities)
            else:
                return "I'm not sure how to handle that automation request."
        except Exception as e:
            logging.error(f"Error in automation skill: {e}")
            return "Sorry, I encountered an error while managing automations."
            
    async def create_routine(self, entities: Dict) -> str:
        """Create a new automation routine"""
        try:
            name = entities.get("name")
            triggers = entities.get("triggers", [])
            actions = entities.get("actions", [])
            
            if not all([name, triggers, actions]):
                return "I need a name, triggers, and actions to create a routine."
                
            config = {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "description": entities.get("description"),
                "enabled": True,
                "triggers": triggers,
                "actions": actions
            }
            
            auto_id = self.controller.create_automation(config)
            
            if auto_id:
                return f"Created routine: {name}"
            else:
                return "Sorry, I couldn't create that routine."
                
        except Exception as e:
            logging.error(f"Error creating routine: {e}")
            return "Sorry, I couldn't create that routine."
            
    async def delete_routine(self, entities: Dict) -> str:
        """Delete an automation routine"""
        try:
            routine_id = entities.get("routine_id")
            if not routine_id:
                return "Which routine would you like to delete?"
                
            success = self.controller.delete_automation(routine_id)
            
            if success:
                return f"Deleted routine: {routine_id}"
            else:
                return f"Couldn't find routine: {routine_id}"
                
        except Exception as e:
            logging.error(f"Error deleting routine: {e}")
            return "Sorry, I couldn't delete that routine."
            
    async def list_routines(self) -> str:
        """List all automation routines"""
        try:
            if not self.controller.automations:
                return "No routines found."
                
            response = "Here are your routines:\n\n"
            
            for auto_id, automation in self.controller.automations.items():
                status = "enabled" if automation.enabled else "disabled"
                response += f"- {automation.name} ({status})\n"
                if automation.description:
                    response += f"  {automation.description}\n"
                response += "\n"
                
            return response
            
        except Exception as e:
            logging.error(f"Error listing routines: {e}")
            return "Sorry, I couldn't list your routines."
            
    async def toggle_routine(self, entities: Dict) -> str:
        """Enable or disable a routine"""
        try:
            routine_id = entities.get("routine_id")
            enable = entities.get("enable", True)
            
            if not routine_id:
                return "Which routine would you like to toggle?"
                
            success = self.controller.toggle_automation(routine_id, enable)
            
            if success:
                status = "enabled" if enable else "disabled"
                return f"Routine '{routine_id}' is now {status}"
            else:
                return f"Couldn't find routine: {routine_id}"
                
        except Exception as e:
            logging.error(f"Error toggling routine: {e}")
            return "Sorry, I couldn't toggle that routine."
            
    async def trigger_routine(self, entities: Dict) -> str:
        """Manually trigger a routine"""
        try:
            routine_id = entities.get("routine_id")
            if not routine_id:
                return "Which routine would you like to trigger?"
                
            success = await self.controller.execute_automation(routine_id)
            
            if success:
                return f"Triggered routine: {routine_id}"
            else:
                return f"Couldn't trigger routine: {routine_id}"
                
        except Exception as e:
            logging.error(f"Error triggering routine: {e}")
            return "Sorry, I couldn't trigger that routine."
            
    async def trigger_ifttt(self, entities: Dict) -> str:
        """Trigger an IFTTT webhook"""
        try:
            event = entities.get("event")
            if not event:
                return "Which IFTTT event would you like to trigger?"
                
            # Get optional values
            value1 = entities.get("value1")
            value2 = entities.get("value2")
            value3 = entities.get("value3")
            
            success = await self.controller.trigger_ifttt_webhook(
                event, value1, value2, value3)
                
            if success:
                return f"Triggered IFTTT event: {event}"
            else:
                return f"Failed to trigger IFTTT event: {event}"
                
        except Exception as e:
            logging.error(f"Error triggering IFTTT: {e}")
            return "Sorry, I couldn't trigger that IFTTT event."
            
    # This method will be called by the AutomationController
    async def execute_action(self, action):
        """Execute an automation action using registered skills"""
        try:
            skill = self.skill_registry.get(action.skill)
            if not skill:
                raise ValueError(f"Skill not found: {action.skill}")
                
            response = await skill.handle_intent(action.intent, action.entities)
            return response
            
        except Exception as e:
            logging.error(f"Error executing action: {e}")
            raise
