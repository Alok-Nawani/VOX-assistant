import os
import json
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, time
import yaml
import logging
import asyncio
from pydantic import BaseModel

class Trigger(BaseModel):
    """Model for automation trigger"""
    type: str  # time, event, condition
    parameters: Dict
    
class Action(BaseModel):
    """Model for automation action"""
    skill: str
    intent: str
    entities: Dict
    
class Automation(BaseModel):
    """Model for automation rule"""
    id: str
    name: str
    description: Optional[str]
    enabled: bool
    triggers: List[Trigger]
    actions: List[Action]
    
class AutomationController:
    """Controller for managing automations and routines"""
    
    def __init__(self):
        """Initialize automation controller"""
        self.automations: Dict[str, Automation] = {}
        self.ifttt_key = os.getenv("IFTTT_WEBHOOK_KEY")
        self.running_automations: Dict[str, asyncio.Task] = {}
        
    async def load_automations(self, config_path: str = "configs/automations.yml"):
        """Load automations from configuration file"""
        try:
            if not os.path.exists(config_path):
                return
                
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            for auto_config in config.get('automations', []):
                automation = Automation(
                    id=auto_config['id'],
                    name=auto_config['name'],
                    description=auto_config.get('description'),
                    enabled=auto_config.get('enabled', True),
                    triggers=[Trigger(**t) for t in auto_config['triggers']],
                    actions=[Action(**a) for a in auto_config['actions']]
                )
                self.automations[automation.id] = automation
                
            await self._start_automation_monitors()
            
        except Exception as e:
            logging.error(f"Error loading automations: {e}")
            
    async def _start_automation_monitors(self):
        """Start monitoring tasks for time-based automations"""
        for auto_id, automation in self.automations.items():
            if not automation.enabled:
                continue
                
            for trigger in automation.triggers:
                if trigger.type == "time":
                    task = asyncio.create_task(
                        self._monitor_time_trigger(auto_id, trigger))
                    self.running_automations[auto_id] = task
                    
    async def _monitor_time_trigger(self, auto_id: str, trigger: Trigger):
        """Monitor a time-based trigger"""
        try:
            while True:
                now = datetime.now()
                trigger_time = datetime.strptime(
                    trigger.parameters['time'], "%H:%M").time()
                
                # Calculate time until next trigger
                next_trigger = datetime.combine(
                    now.date() if now.time() < trigger_time else now.date(),
                    trigger_time
                )
                if next_trigger < now:
                    next_trigger = next_trigger.replace(day=now.day + 1)
                    
                # Wait until trigger time
                await asyncio.sleep((next_trigger - now).total_seconds())
                
                # Execute automation actions
                await self.execute_automation(auto_id)
                
        except Exception as e:
            logging.error(f"Error in time trigger monitor: {e}")
            
    async def execute_automation(self, auto_id: str) -> bool:
        """Execute an automation's actions"""
        try:
            automation = self.automations.get(auto_id)
            if not automation or not automation.enabled:
                return False
                
            for action in automation.actions:
                try:
                    await self.execute_action(action)
                except Exception as e:
                    logging.error(f"Error executing action: {e}")
                    
            return True
            
        except Exception as e:
            logging.error(f"Error executing automation: {e}")
            return False
            
    async def execute_action(self, action: Action):
        """Execute a single action"""
        # This will be implemented by the AutomationSkill to route to appropriate skill
        pass
        
    async def trigger_ifttt_webhook(self, event: str, value1: str = None,
                                  value2: str = None, value3: str = None) -> bool:
        """Trigger an IFTTT webhook"""
        try:
            if not self.ifttt_key:
                raise ValueError("IFTTT webhook key not configured")
                
            url = f"https://maker.ifttt.com/trigger/{event}/with/key/{self.ifttt_key}"
            
            data = {}
            if value1: data['value1'] = value1
            if value2: data['value2'] = value2
            if value3: data['value3'] = value3
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error triggering IFTTT webhook: {e}")
            return False
            
    def create_automation(self, config: Dict) -> Optional[str]:
        """Create a new automation"""
        try:
            automation = Automation(
                id=config['id'],
                name=config['name'],
                description=config.get('description'),
                enabled=config.get('enabled', True),
                triggers=[Trigger(**t) for t in config['triggers']],
                actions=[Action(**a) for a in config['actions']]
            )
            
            self.automations[automation.id] = automation
            
            # Start monitoring if it's a time-based automation
            for trigger in automation.triggers:
                if trigger.type == "time" and automation.enabled:
                    task = asyncio.create_task(
                        self._monitor_time_trigger(automation.id, trigger))
                    self.running_automations[automation.id] = task
                    
            return automation.id
            
        except Exception as e:
            logging.error(f"Error creating automation: {e}")
            return None
            
    def delete_automation(self, auto_id: str) -> bool:
        """Delete an automation"""
        try:
            if auto_id in self.running_automations:
                self.running_automations[auto_id].cancel()
                del self.running_automations[auto_id]
                
            if auto_id in self.automations:
                del self.automations[auto_id]
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error deleting automation: {e}")
            return False
            
    def toggle_automation(self, auto_id: str, enabled: bool) -> bool:
        """Enable or disable an automation"""
        try:
            if auto_id not in self.automations:
                return False
                
            automation = self.automations[auto_id]
            automation.enabled = enabled
            
            # Handle running tasks
            if enabled:
                for trigger in automation.triggers:
                    if trigger.type == "time":
                        task = asyncio.create_task(
                            self._monitor_time_trigger(auto_id, trigger))
                        self.running_automations[auto_id] = task
            elif auto_id in self.running_automations:
                self.running_automations[auto_id].cancel()
                del self.running_automations[auto_id]
                
            return True
            
        except Exception as e:
            logging.error(f"Error toggling automation: {e}")
            return False
