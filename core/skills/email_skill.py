from typing import Dict, Any
from .base_skill import BaseSkill
from ..tools.email_manager import EmailManager
import logging

class EmailSkill(BaseSkill):
    """Skill for managing emails"""
    
    def __init__(self):
        super().__init__("email")
        self.email_manager = EmailManager()
        self.sessions = {} # user_id -> {"recipient": null, "intent": null, "step": "need_recipient"}
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "")
        history = params.get("history", [])
        user_id = params.get("user_id", 1)
        is_followup = params.get("is_followup", False)
        
        # Multi-turn conversational flow
        if is_followup and user_id in self.sessions:
            session = self.sessions[user_id]
            if session["step"] == "need_recipient":
                session["recipient"] = text.strip()
                if not session["intent"]:
                    session["step"] = "need_intent"
                    return {"success": True, "message": f"Got it, to {session['recipient']}. What's the subject and message?", "keep_active": True}
                else:
                    session["step"] = "ready"
            elif session["step"] == "need_intent":
                session["intent"] = text.strip()
                session["step"] = "ready"
                
            if session["step"] == "ready":
                recipient = session["recipient"]
                intent = session["intent"]
                del self.sessions[user_id]
                return await self._frame_and_send(recipient, intent, history, user_id)
        
        # 1. Detect if it's a read or send request
        if any(word in text.lower() for word in ["read", "check", "inbox", "list"]):
            return await self._handle_read(text, {"user_id": user_id})
            
        # 2. Use AI to intelligently extract recipient and intent
        import google.generativeai as genai
        import json
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        extraction_prompt = (
            "Analyze this Email request: " + text + "\n\n"
            "TASK: Separate the RECIPIENT (Email or Name) from the MESSAGE (the actual intent/words).\n"
            "CLEANING RULES:\n"
            "- If the command doesn't mention a recipient, return null for recipient.\n"
            "- If the command doesn't mention a message, return null for intent.\n"
            "EXAMPLE: 'email nidhin@gmail.com asking for coffee'\n"
            "OUTPUT: {\"recipient\": \"nidhin@gmail.com\", \"intent\": \"asking for coffee\"}\n\n"
            "EXAMPLE: 'send an email'\n"
            "OUTPUT: {\"recipient\": null, \"intent\": null}\n\n"
            "NEGATIVE RULE: NEVER put the message content into the 'recipient' field.\n"
            "Return ONLY JSON: {\"recipient\": \"...\", \"intent\": \"...\"}"
        )
        
        recipient, intent = None, None
        import re
        def get_fallback_info(t):
            t_low = t.lower().strip()
            # Improved regex to skip 'to' and handle 'asking/telling/that'
            match = re.search(r"email\s+(?:to\s+)?([a-zA-Z0-9@\.-]+)\s+(?:about|regarding|that|is|asking|telling|to)\s+(.*)", t_low)
            if match:
                return match.group(1).strip(), match.group(2).strip()
            
            # Simple recipient match
            match_simple = re.search(r"email\s+(?:to\s+)?([a-zA-Z0-9@\.-]+)", t_low)
            if match_simple:
                return match_simple.group(1).strip(), t
                
            return None, t

        recipient, intent = None, text
        try:
            extraction = model.generate_content(extraction_prompt)
            data = extraction.text.strip()
            if "```json" in data: data = data.split("```json")[1].split("```")[0].strip()
            info = json.loads(data)
            recipient = info.get("recipient")
            intent = info.get("intent")
            if str(recipient).lower() in ["null", "none", "", "mail", "email", "to"]:
                recipient = None
            if str(intent).lower() in ["null", "none", "", "email"]:
                intent = None
        except Exception as e:
            logging.warning(f"Email AI Extraction failed: {e}. Using fallback.")
            recipient, intent = get_fallback_info(text)

        if not recipient and not intent:
            self.sessions[user_id] = {"recipient": None, "intent": None, "step": "need_recipient"}
            return {"success": True, "message": "Who would you like me to email?", "keep_active": True}
        elif not recipient:
            self.sessions[user_id] = {"recipient": None, "intent": intent, "step": "need_recipient"}
            return {"success": True, "message": f"Got the message. Who should I send the email to?", "keep_active": True}
        elif not intent:
            self.sessions[user_id] = {"recipient": recipient, "intent": None, "step": "need_intent"}
            return {"success": True, "message": f"What's the subject and message for {recipient}?", "keep_active": True}
            
        return await self._frame_and_send(recipient, intent, history, user_id)

    async def _frame_and_send(self, recipient: str, intent: str, history: list, user_id: int) -> Dict[str, Any]:
        """Frames and sends the email"""
        from ..ai.framer import MessageFramer
        framer = MessageFramer()
        
        subject = "Message from Alok"
        body = intent
        
        try:
            # Enhanced Framing: Pass recipient context for better tone detection
            framer_context = f"Recipient: {recipient} | History: {str(history[-3:])}"
            framed = await framer.frame_communication(intent, "email", context=framer_context)
            subject = framed.get("subject", f"Message from Alok regarding {intent[:20]}")
            body = framed.get("body", intent)
        except Exception as e:
            logging.error(f"Vox System: Email AI Framing failed ({e}), using generic template.")
        
        print(f"Vox AI Framing: Email to {recipient} -> Subject: {subject}")
        
        success = await self.email_manager.send_email(recipient, subject, body, user_id=user_id)
        
        if success:
            return {"success": True, "message": f"Sent that email to {recipient}."}
        else:
            return {"success": False, "message": f"I drafted the email to {recipient}, but couldn't send it. Check setup."}

    async def _handle_read(self, text: str, entities: Dict) -> Dict[str, Any]:
        user_id = entities.get("user_id", 1)
        emails = await self.email_manager.read_emails("INBOX", 3, user_id=user_id)
        if not emails:
            return {"success": True, "message": "Your inbox is looking pretty quiet, Alok. No new emails."}
            
        msg = "Alright, here are your latest emails: "
        for email in emails:
            msg += f"From {email['from']} about '{email['subject']}'. "
            
        return {"success": True, "message": msg}

    async def _handle_send(self, text: str, entities: Dict) -> Dict[str, Any]:
        if entities.get("is_followup"):
            return {"success": True, "message": f"Got it, Alok. I've sent that off to {text} for you."}

        return {
            "success": True,
            "message": "I've drafted that for you. Who should I send it to?",
            "keep_active": True
        }

    async def _handle_search(self, text: str, entities: Dict) -> Dict[str, Any]:
        user_id = entities.get("user_id", 1)
        query = text.split("search for")[-1].strip() if "search for" in text else ""
        if not query:
            return {"success": False, "message": "What should I look for in your emails, Alok?"}
            
        emails = await self.email_manager.search_emails(query, user_id=user_id)
        if not emails:
            return {"success": True, "message": f"I couldn't find any emails about '{query}'."}
            
        return {"success": True, "message": f"I found {len(emails)} emails matching that. The most recent one is from {emails[0]['from']}."}
