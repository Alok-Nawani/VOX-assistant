from typing import Dict, List, Optional
from .base_skill import BaseSkill
from ..tools.home_assistant import HomeAssistantAPI, Device
import logging
import os

class SmartHomeSkill(BaseSkill):
    """Skill for controlling smart home devices"""
    
    def __init__(self):
        super().__init__()
        self.name = "smart_home"
        self.ha_api = HomeAssistantAPI()
        self.devices: List[Device] = []
        self.initialized = False
        
    async def initialize(self):
        """Initialize connection to Home Assistant"""
        if self.initialized:
            return
            
        try:
            ha_url = os.getenv("HASS_URL", "http://localhost:8123/api")
            ha_token = os.getenv("HASS_TOKEN")
            
            if not ha_token:
                raise ValueError("Home Assistant token not found in environment variables")
                
            await self.ha_api.connect(ha_url, ha_token)
            self.devices = await self.ha_api.get_devices()
            self.initialized = True
            
        except Exception as e:
            logging.error(f"Error initializing smart home skill: {e}")
            raise
            
    async def handle_intent(self, intent: str, entities: Dict) -> str:
        """Handle smart home control intents"""
        try:
            if not self.initialized:
                await self.initialize()
                
            if intent == "device_control":
                return await self.control_device(entities)
            elif intent == "device_status":
                return await self.get_device_status(entities)
            elif intent == "list_devices":
                return await self.list_devices(entities)
            else:
                return "I'm not sure how to handle that smart home request."
                
        except Exception as e:
            logging.error(f"Error in smart home skill: {e}")
            return "Sorry, I encountered an error while controlling your smart home."
            
    def _find_device(self, query: str) -> Optional[Device]:
        """Find a device by name or ID"""
        query = query.lower()
        for device in self.devices:
            if query in device.name.lower() or query in device.id.lower():
                return device
        return None
        
    async def control_device(self, entities: Dict) -> str:
        """Control a smart home device"""
        try:
            device_name = entities.get("device")
            action = entities.get("action")
            
            if not all([device_name, action]):
                return "I need both a device name and action to control a device."
                
            device = self._find_device(device_name)
            if not device:
                return f"I couldn't find a device matching '{device_name}'."
                
            # Handle different types of actions
            if action in ["on", "off"]:
                command = f"turn_{action}"
                success = await self.ha_api.control_device(device.id, command)
            elif action.startswith("set"):
                # Handle set temperature, brightness, etc.
                param_type = action.split()[1]  # e.g., "temperature", "brightness"
                value = entities.get("value")
                if not value:
                    return f"I need a value to set the {param_type}."
                    
                success = await self.ha_api.control_device(
                    device.id,
                    "set",
                    {param_type: value}
                )
            else:
                return f"I don't know how to {action} a {device.type}."
                
            if success:
                return f"OK, {action} {device.name}"
            else:
                return f"Sorry, I couldn't {action} {device.name}"
                
        except Exception as e:
            logging.error(f"Error controlling device: {e}")
            return "Sorry, I couldn't control that device."
            
    async def get_device_status(self, entities: Dict) -> str:
        """Get status of a smart home device"""
        try:
            device_name = entities.get("device")
            if not device_name:
                return "Which device would you like to check?"
                
            device = self._find_device(device_name)
            if not device:
                return f"I couldn't find a device matching '{device_name}'."
                
            state = await self.ha_api.get_device_state(device.id)
            if not state:
                return f"Sorry, I couldn't get the status of {device.name}"
                
            # Format response based on device type
            if device.type == "light":
                brightness = state["attributes"].get("brightness", 0)
                return f"{device.name} is {state['state']}" + \
                       (f" at {int(brightness/255*100)}% brightness" if state['state'] == 'on' else "")
                       
            elif device.type == "climate":
                current_temp = state["attributes"].get("current_temperature")
                target_temp = state["attributes"].get("temperature")
                return f"{device.name} is {state['state']}, " + \
                       f"current temperature is {current_temp}°C, " + \
                       f"set to {target_temp}°C"
                       
            else:
                return f"{device.name} is {state['state']}"
                
        except Exception as e:
            logging.error(f"Error getting device status: {e}")
            return "Sorry, I couldn't get the device status."
            
    async def list_devices(self, entities: Dict) -> str:
        """List all smart home devices"""
        try:
            # Refresh device list
            self.devices = await self.ha_api.get_devices()
            
            if not self.devices:
                return "No smart home devices found."
                
            # Group devices by room
            devices_by_room = {}
            for device in self.devices:
                room = device.room or "Other"
                if room not in devices_by_room:
                    devices_by_room[room] = []
                devices_by_room[room].append(device)
                
            # Format response
            response = "Here are your smart home devices:\n\n"
            for room, devices in devices_by_room.items():
                response += f"{room}:\n"
                for device in devices:
                    response += f"- {device.name} ({device.type})\n"
                response += "\n"
                
            return response
            
        except Exception as e:
            logging.error(f"Error listing devices: {e}")
            return "Sorry, I couldn't list the devices."
