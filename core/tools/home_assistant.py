from typing import Dict, List, Optional
import asyncio
import aiohttp
import logging
from pydantic import BaseModel

class Device(BaseModel):
    """Model for smart home device"""
    id: str
    name: str
    type: str  # light, thermostat, switch, etc.
    state: Dict  # Current state of the device
    room: Optional[str] = None

class HomeAssistantAPI:
    """Client for Home Assistant API"""
    
    def __init__(self):
        """Initialize Home Assistant API client"""
        self.base_url = "http://localhost:8123/api"  # Default Home Assistant URL
        self.token = None  # Will be loaded from config
        self.session = None
        
    async def connect(self, url: str, token: str):
        """Connect to Home Assistant instance"""
        self.base_url = url
        self.token = token
        self.session = aiohttp.ClientSession(headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
        
    async def close(self):
        """Close the API connection"""
        if self.session:
            await self.session.close()
            
    async def get_devices(self) -> List[Device]:
        """Get list of all devices"""
        try:
            async with self.session.get(f"{self.base_url}/states") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get devices: {response.status}")
                    
                data = await response.json()
                devices = []
                
                for entity in data:
                    # Parse entity ID to get device type
                    domain = entity["entity_id"].split(".")[0]
                    
                    # Only include supported device types
                    if domain in ["light", "switch", "climate", "media_player"]:
                        devices.append(Device(
                            id=entity["entity_id"],
                            name=entity["attributes"].get("friendly_name", entity["entity_id"]),
                            type=domain,
                            state=entity["state"],
                            room=entity["attributes"].get("room")
                        ))
                        
                return devices
                
        except Exception as e:
            logging.error(f"Error getting devices: {e}")
            return []
            
    async def control_device(self, device_id: str, command: str, params: Dict = None) -> bool:
        """Control a smart home device
        
        Args:
            device_id: The entity ID of the device
            command: The service to call (turn_on, turn_off, etc.)
            params: Additional parameters for the service call
        """
        try:
            domain = device_id.split(".")[0]
            service_data = {"entity_id": device_id}
            if params:
                service_data.update(params)
                
            async with self.session.post(
                f"{self.base_url}/services/{domain}/{command}",
                json=service_data
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logging.error(f"Error controlling device: {e}")
            return False
            
    async def get_device_state(self, device_id: str) -> Optional[Dict]:
        """Get current state of a device"""
        try:
            async with self.session.get(f"{self.base_url}/states/{device_id}") as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                return {
                    "state": data["state"],
                    "attributes": data["attributes"]
                }
                
        except Exception as e:
            logging.error(f"Error getting device state: {e}")
            return None
