from typing import Dict
from ..tools.whatsapp_automation import WhatsAppAutomation
import logging

class MessageHandler:
    """Handles message sending across different platforms"""
    
    def __init__(self):
        """Initialize message handlers"""
        self.whatsapp = WhatsAppAutomation()
        
    async def send_message(self, recipient: str, message: str, platform: str = "whatsapp") -> bool:
        """Send a message using the specified platform
        
        Args:
            recipient: The message recipient (phone number or contact name)
            message: The message content to send
            platform: The messaging platform to use (default: whatsapp)
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            if platform.lower() == "whatsapp":
                return await self.whatsapp.send_whatsapp_message(recipient, message)
            else:
                logging.error(f"Unsupported messaging platform: {platform}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False
            
    async def handle_message_intent(self, input_data: Dict) -> Dict:
        """Handle message sending intent
        
        Args:
            input_data: Dictionary containing intent data with:
                - recipient: The message recipient
                - message: The message content
                - platform: The messaging platform (optional)
                
        Returns:
            Dict: Response indicating success or failure
        """
        recipient = input_data.get("recipient")
        message = input_data.get("message")
        platform = input_data.get("platform", "whatsapp")
        
        if not all([recipient, message]):
            missing = []
            if not recipient:
                missing.append("recipient")
            if not message:
                missing.append("message content")
                
            return {
                "response_type": "slot_request",
                "slot": missing[0],
                "message": f"Please provide the {' and '.join(missing)}"
            }
            
        success = await self.send_message(recipient, message, platform)
        
        if success:
            return {
                "response_type": "success",
                "message": f"Message sent to {recipient} on {platform}",
                "data": {
                    "recipient": recipient,
                    "message": message,
                    "platform": platform,
                    "status": "sent"
                }
            }
        else:
            return {
                "response_type": "error",
                "message": f"Failed to send message to {recipient}. Please try again.",
                "data": {
                    "recipient": recipient,
                    "message": message,
                    "platform": platform,
                    "status": "failed"
                }
            }
