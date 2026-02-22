import os
import json
import logging
import re
import google.generativeai as genai
from typing import Optional, Dict

class MessageFramer:
    """Uses Gemini to intelligently frame messages for WhatsApp and Email"""
    
    def __init__(self):
        # Configure genai with the key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        # Use a high-quality model for framing
        self.model = genai.GenerativeModel('gemini-flash-lite-latest')

    async def frame_communication(self, intent_text: str, medium: str, context: Optional[str] = None) -> Dict[str, str]:
        """
        Intelligently frame a message based on user raw intent.
        
        Args:
            intent_text: The raw user command or content (e.g., "asking if she had lunch")
            medium: 'whatsapp' or 'email'
            context: Optional previous conversation for better framing
            
        Returns:
            Dict containing 'body' (and 'subject' for email)
        """
        if not self.model:
            return {"body": intent_text}

        try:
            if medium == "whatsapp":
                prompt = (
                    "You are VOX, Alok's Neural Social Strategist. You write EXACTLY as ALOK. \n\n"
                    f"USER INTENT: {intent_text}\n"
                    f"RECIPIENT: {context}\n\n"
                    "SOCIAL ANALYSIS:\n"
                    "1. PERSPECTIVE: Write in the FIRST PERSON ('I', 'me', 'my'). \n"
                    "2. VIBE: Identify the required emotion (Cheesy, Serious, Playful). Sound natural, use contractions.\n\n"
                    "RULES:\n"
                    "- Only return the message itself. No quotes. No preamble.\n"
                    "- Never say 'He says' or 'I am writing this for him'. Just the message."
                )
            else: # email
                prompt = (
                    "You are VOX, Alok's Neural Social Strategist. You write as ALOK, in the FIRST PERSON ('I', 'me', 'my'). \n\n"
                    f"USER INTENT: {intent_text}\n"
                    f"CONTEXT: {context if context else 'Personal/Professional'}\n\n"
                    "SOCIAL ANALYSIS:\n"
                    "1. VIBE: Identify if it's Cheesy, Serious, or Professional. Match it perfectly.\n"
                    "2. PERSPECTIVE: ALWAYS write as Alok. Never use phrases like 'Alok wants to say' or 'I am writing regarding her'.\n\n"
                    "CONSTRAINTS:\n"
                    "- Subject: Creative and clicked-focused.\n"
                    "- Body: Must have a tailored greeting, an natural first-person body, and a personalized sign-off.\n\n"
                    "Return ONLY JSON: {\"subject\": \"...\", \"body\": \"...\"}"
                )

            logging.info(f"Neural Framing engaged for {medium}")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            logging.info(f"Raw Intelligence: {result_text[:100]}...")
            
            if medium == "whatsapp":
                return {"body": result_text}
            else:
                # Robust JSON extraction
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                else:
                    raise ValueError("Neural output refused to be parsed.")

        except Exception as e:
            logging.error(f"Neural Framing Core Failure: {e}")
            
            # Universal Humanized Backup (No more 'regarding...')
            clean_intent = intent_text.strip().capitalize()
            if medium == "email":
                return {
                    "subject": f"Message regarding: {intent_text[:30]}",
                    "body": f"Hi,\n\n{clean_intent}.\n\nBest,\nAlok"
                }
            return {"body": clean_intent}
