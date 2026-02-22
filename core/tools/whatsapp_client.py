import os
import aiohttp
from typing import Optional
import logging
from dotenv import load_dotenv

class WhatsAppClient:
    """Meta Cloud API client for WhatsApp Business Platform"""
    
    def __init__(self):
        """Initialize WhatsApp client with Meta Cloud API credentials"""
        load_dotenv()
        
        self.access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.api_version = 'v17.0'  # Meta API version
        
        if not all([self.access_token, self.phone_number_id]):
            raise ValueError("WhatsApp API credentials not found in environment")
            
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        
    async def send_message(self, to: str, message: str) -> bool:
        """Send a WhatsApp message using Meta Cloud API
        
        Args:
            to: Phone number in international format (e.g., "1234567890")
            message: The message text to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Format phone number (remove any non-digits and ensure it starts with country code)
            phone = ''.join(filter(str.isdigit, to))
            if not phone.startswith('1'):  # Assuming US numbers, adjust as needed
                phone = '1' + phone
                
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {'body': message}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        logging.info(f"WhatsApp message sent to {to}")
                        return True
                    else:
                        error_data = await response.json()
                        logging.error(f"Failed to send WhatsApp message: {error_data}")
                        return False
                        
        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {e}")
            return False
