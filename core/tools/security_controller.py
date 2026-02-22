import os
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging
import asyncio
from pydantic import BaseModel

class SecurityEvent(BaseModel):
    """Model for security events"""
    id: str
    type: str  # motion, door, window, alarm
    location: str
    timestamp: datetime
    status: str
    details: Optional[Dict] = None

class SecurityZone(BaseModel):
    """Model for security zones"""
    id: str
    name: str
    armed: bool
    sensors: List[str]

class SecurityController:
    """Controller for security system integration"""
    
    def __init__(self):
        """Initialize security controller"""
        self.api_url = os.getenv("SECURITY_API_URL")
        self.api_key = os.getenv("SECURITY_API_KEY")
        self.zones: Dict[str, SecurityZone] = {}
        self.event_listeners: List = []
        self._monitoring_task = None
        
    async def initialize(self):
        """Initialize connection to security system"""
        if not all([self.api_url, self.api_key]):
            raise ValueError("Security system API configuration missing")
            
        await self._load_zones()
        self._start_monitoring()
        
    async def _load_zones(self):
        """Load security zones configuration"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(f"{self.api_url}/zones", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to load zones: {response.status}")
                        
                    data = await response.json()
                    self.zones = {
                        zone["id"]: SecurityZone(**zone)
                        for zone in data["zones"]
                    }
                    
        except Exception as e:
            logging.error(f"Error loading security zones: {e}")
            raise
            
    def _start_monitoring(self):
        """Start monitoring for security events"""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_events())
            
    async def _monitor_events(self):
        """Monitor security events in real-time"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "text/event-stream"
                }
                
                async with session.get(
                    f"{self.api_url}/events/stream",
                    headers=headers
                ) as response:
                    while True:
                        event = await response.content.readline()
                        if not event:
                            break
                            
                        data = event.decode().strip()
                        if data.startswith("data: "):
                            event_data = json.loads(data[6:])
                            await self._handle_event(SecurityEvent(**event_data))
                            
        except Exception as e:
            logging.error(f"Error in event monitoring: {e}")
            # Retry after delay
            await asyncio.sleep(5)
            self._start_monitoring()
            
    async def _handle_event(self, event: SecurityEvent):
        """Handle incoming security events"""
        try:
            # Notify all registered listeners
            for listener in self.event_listeners:
                await listener(event)
        except Exception as e:
            logging.error(f"Error handling security event: {e}")
            
    def add_event_listener(self, callback):
        """Register a callback for security events"""
        self.event_listeners.append(callback)
        
    def remove_event_listener(self, callback):
        """Remove a registered event callback"""
        if callback in self.event_listeners:
            self.event_listeners.remove(callback)
            
    async def arm_system(self, mode: str = "away") -> bool:
        """Arm the security system
        
        Args:
            mode: Arming mode (away, stay, night)
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = {"mode": mode}
                
                async with session.post(
                    f"{self.api_url}/arm",
                    headers=headers,
                    json=data
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error arming system: {e}")
            return False
            
    async def disarm_system(self, code: str = None) -> bool:
        """Disarm the security system"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = {"code": code} if code else {}
                
                async with session.post(
                    f"{self.api_url}/disarm",
                    headers=headers,
                    json=data
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error disarming system: {e}")
            return False
            
    async def get_system_status(self) -> Optional[Dict]:
        """Get current security system status"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.get(
                    f"{self.api_url}/status",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        return None
                        
                    return await response.json()
                    
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return None
            
    async def get_recent_events(self, limit: int = 5) -> List[SecurityEvent]:
        """Get recent security events"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {"limit": limit}
                
                async with session.get(
                    f"{self.api_url}/events",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    return [SecurityEvent(**event) for event in data["events"]]
                    
        except Exception as e:
            logging.error(f"Error getting recent events: {e}")
            return []
            
    async def trigger_panic(self, type: str = "police") -> bool:
        """Trigger panic alarm
        
        Args:
            type: Type of panic (police, fire, medical)
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = {"type": type}
                
                async with session.post(
                    f"{self.api_url}/panic",
                    headers=headers,
                    json=data
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error triggering panic: {e}")
            return False
