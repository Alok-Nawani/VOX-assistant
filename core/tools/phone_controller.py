import os
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

class Contact(BaseModel):
    """Model for phone contacts"""
    id: str
    name: str
    numbers: List[str]
    email: Optional[str] = None

class Message(BaseModel):
    """Model for SMS messages"""
    id: str
    contact: str
    text: str
    timestamp: datetime
    incoming: bool

class Call(BaseModel):
    """Model for phone calls"""
    id: str
    contact: str
    timestamp: datetime
    duration: Optional[int] = None
    status: str  # incoming, outgoing, missed
    recording_url: Optional[str] = None

class PhoneController:
    """Controller for phone integration"""
    
    def __init__(self):
        """Initialize phone controller"""
        self.api_url = os.getenv("PHONE_API_URL")
        self.api_key = os.getenv("PHONE_API_KEY")
        self.contacts: Dict[str, Contact] = {}
        
    async def initialize(self):
        """Initialize phone integration"""
        if not all([self.api_url, self.api_key]):
            raise ValueError("Phone API configuration missing")
            
        await self._load_contacts()
        
    async def _load_contacts(self):
        """Load phone contacts"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.api_url}/contacts",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to load contacts: {response.status}")
                        
                    data = await response.json()
                    self.contacts = {
                        contact["id"]: Contact(**contact)
                        for contact in data["contacts"]
                    }
                    
        except Exception as e:
            logging.error(f"Error loading contacts: {e}")
            raise
            
    async def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS message
        
        Args:
            to: Phone number or contact name
            message: Message text
        """
        try:
            # Resolve contact name to number if needed
            number = await self._resolve_contact(to)
            if not number:
                return False
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = {
                    "to": number,
                    "message": message
                }
                
                async with session.post(
                    f"{self.api_url}/sms/send",
                    headers=headers,
                    json=data
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error sending SMS: {e}")
            return False
            
    async def get_messages(self, limit: int = 5) -> List[Message]:
        """Get recent messages"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {"limit": limit}
                
                async with session.get(
                    f"{self.api_url}/sms",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    return [Message(**msg) for msg in data["messages"]]
                    
        except Exception as e:
            logging.error(f"Error getting messages: {e}")
            return []
            
    async def make_call(self, to: str) -> bool:
        """Make a phone call
        
        Args:
            to: Phone number or contact name
        """
        try:
            # Resolve contact name to number if needed
            number = await self._resolve_contact(to)
            if not number:
                return False
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = {"to": number}
                
                async with session.post(
                    f"{self.api_url}/calls/make",
                    headers=headers,
                    json=data
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error making call: {e}")
            return False
            
    async def get_call_history(self, limit: int = 5) -> List[Call]:
        """Get recent call history"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {"limit": limit}
                
                async with session.get(
                    f"{self.api_url}/calls",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        return []
                        
                    data = await response.json()
                    return [Call(**call) for call in data["calls"]]
                    
        except Exception as e:
            logging.error(f"Error getting call history: {e}")
            return []
            
    async def _resolve_contact(self, contact: str) -> Optional[str]:
        """Resolve contact name to phone number"""
        try:
            # If it's already a phone number, return it
            if contact.replace('+', '').replace('-', '').isdigit():
                return contact
                
            # Search contacts by name
            for c in self.contacts.values():
                if contact.lower() in c.name.lower():
                    return c.numbers[0] if c.numbers else None
                    
            return None
            
        except Exception as e:
            logging.error(f"Error resolving contact: {e}")
            return None
            
    def format_message(self, message: Message) -> str:
        """Format a message for speech output"""
        try:
            time_str = message.timestamp.strftime("%I:%M %p")
            direction = "from" if message.incoming else "to"
            return f"Message {direction} {message.contact} at {time_str}:\n{message.text}\n"
        except Exception as e:
            logging.error(f"Error formatting message: {e}")
            return ""
            
    def format_call(self, call: Call) -> str:
        """Format a call for speech output"""
        try:
            time_str = call.timestamp.strftime("%I:%M %p")
            if call.status == "missed":
                return f"Missed call from {call.contact} at {time_str}\n"
                
            duration = f" ({call.duration} seconds)" if call.duration else ""
            return f"{call.status.title()} call with {call.contact} at {time_str}{duration}\n"
        except Exception as e:
            logging.error(f"Error formatting call: {e}")
            return ""
