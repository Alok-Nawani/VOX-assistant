import json
import logging
import re
from .base_skill import BaseSkill
from ..tools.whatsapp_automation import WhatsAppAutomation
from typing import Dict, Any

class WhatsAppSkill(BaseSkill):
    """Skill for sending WhatsApp messages using GUI automation"""
    
    def __init__(self):
        super().__init__("whatsapp")
        self.automation = WhatsAppAutomation()
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
                # The text is likely the recipient
                session["recipient"] = text.strip()
                if not session["intent"]:
                    session["step"] = "need_intent"
                    return {"success": True, "message": f"Got it, to {session['recipient']}. What should I say?", "keep_active": True}
                else:
                    session["step"] = "ready"
            elif session["step"] == "need_intent":
                # The text is the intent
                session["intent"] = text.strip()
                session["step"] = "ready"
                
            if session["step"] == "ready":
                recipient = session["recipient"]
                intent = session["intent"]
                del self.sessions[user_id]
                return await self._frame_and_send(recipient, intent, history)
        
        # 1. Fallback / Deterministic Extraction (Robustness layer)
        def get_fallback_info(t):
            t_clean = re.sub(r"\s+in\s+whatsapp\b", "", t, flags=re.IGNORECASE).strip()
            t_low = t_clean.lower()
            
            # 1. Pattern: send [Content] to [Name]
            send_to = re.search(r"send\s+(.*)\s+to\s+([a-zA-Z\s]+)", t_low)
            if send_to:
                content = send_to.group(1).strip()
                recipient = send_to.group(2).strip()
                if content == "this" or content == "that":
                    parts = re.split(r"\bsend\b", t_clean, flags=re.IGNORECASE)
                    if len(parts) > 1: content = parts[0].strip()
                return recipient, content
            
            # 2. Pattern: [Content] message to [Name]
            msg_to = re.search(r"(.*)\s+(?:message|msg|whatsapp)\s+to\s+([a-zA-Z\s]+)", t_low)
            if msg_to:
                orig_match = re.search(r"(.*)\s+(?:message|msg|whatsapp)\s+to\s+([a-zA-Z\s]+)", t_clean, flags=re.IGNORECASE)
                return orig_match.group(2).strip(), orig_match.group(1).strip()

            # 3. Refined Greedy: Name (1-3 words) + Condition word
            msg_name = re.search(r"(?:message|msg|whatsapp)\s+([a-zA-Z\s]{1,30}?)\s+(?:is|asking|saying|that|for|telling)\s+(.*)", t_clean, flags=re.IGNORECASE)
            if msg_name:
                recipient = msg_name.group(1).strip()
                if len(recipient.split()) <= 3:
                     return recipient, msg_name.group(2).strip()

            # 4. Atomic Fallback: First word after 'to' or 'message'
            atomic = re.search(r"(?:to|message|msg|whatsapp)\s+([a-zA-Z]+)", t_low)
            if atomic:
                return atomic.group(1).strip(), t.replace(atomic.group(0), "").strip()
                
            return None, t

        # Try AI extraction first
        from ..ai.framer import MessageFramer
        framer = MessageFramer()
        
        import google.generativeai as genai
        model = genai.GenerativeModel('gemini-flash-latest')
        extraction_prompt = (
            "Analyze this WhatsApp command: " + text + "\n\n"
            "TASK: Separate the RECIPIENT (the person's name) from the INTENT (what needs to be said).\n"
            "CLEANING RULES:\n"
            "- If the command doesn't mention a recipient, return null for recipient.\n"
            "- If the command doesn't mention a message, return null for intent.\n"
            "- The INTENT should be a clean summary or the exact message, stripped of 'telling her', 'asking context', or 'that'.\n"
            "- RECIPIENT must be 1-3 words max, or null.\n\n"
            "EXAMPLE: 'send a cheesy msg to Nidhin telling her she looks great'\n"
            "OUTPUT: {\"recipient\": \"Nidhin\", \"intent\": \"she looks great\"}\n\n"
            "EXAMPLE: 'send a whatsapp message'\n"
            "OUTPUT: {\"recipient\": null, \"intent\": null}\n\n"
            "Return ONLY JSON: {\"recipient\": \"...\", \"intent\": \"...\"}"
        )
        
        recipient, intent = None, None
        try:
            # Use async call to prevent blocking
            extraction = await model.generate_content_async(extraction_prompt)
            data = extraction.text.strip()
            logging.info(f"WhatsApp Extraction Raw: {data}")
            
            # Robust JSON block extraction
            json_match = re.search(r'\{.*\}', data, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group(0))
                recipient = info.get("recipient")
                intent = info.get("intent")
                if str(recipient).lower() in ["null", "none", "", "message", "on", "whatsapp"]:
                    recipient = None
                if str(intent).lower() in ["null", "none", "", "whatsapp"]:
                    intent = None
            else:
                raise ValueError("No JSON found")
                
            # Final Safety: If recipient is ridiculously long, AI failed
            if recipient and len(recipient.split()) > 3:
                logging.warning(f"AI hallucinated long recipient: {recipient}. Falling back.")
                recipient, intent = get_fallback_info(text)
                
        except Exception as e:
            logging.warning(f"WhatsApp AI Extraction failed ({e}), using deterministic fallback.")
            recipient, intent = get_fallback_info(text)

        if not recipient and not intent:
            self.sessions[user_id] = {"recipient": None, "intent": None, "step": "need_recipient"}
            return {"success": True, "message": "Who would you like me to send a WhatsApp message to?", "keep_active": True}
        elif not recipient:
            self.sessions[user_id] = {"recipient": None, "intent": intent, "step": "need_recipient"}
            return {"success": True, "message": f"Got the message. Who should I send it to?", "keep_active": True}
        elif not intent:
            self.sessions[user_id] = {"recipient": recipient, "intent": None, "step": "need_intent"}
            return {"success": True, "message": f"What do you want to say to {recipient}?", "keep_active": True}
            
        return await self._frame_and_send(recipient, intent, history)

    async def _frame_and_send(self, recipient: str, intent: str, history: list) -> Dict[str, Any]:
        """Handles the actual framing and sending of the message"""
        from ..ai.framer import MessageFramer
        framer = MessageFramer()
        
        # 2. Frame the message
        message = intent
        try:
            framer_context = f"Recipient: {recipient} | History: {str(history[-2:])}"
            # frame_communication is already async
            framed = await framer.frame_communication(intent, "whatsapp", context=framer_context)
            message = framed.get("body", intent)
        except Exception as e:
            logging.error(f"Vox System: WhatsApp AI Framing failed ({e}), using raw intent.")
            message = intent
        
        print(f"Vox AI: Dispatching to {recipient} -> '{message}'")
        # Unified dispatch
        success = await self.automation.send_whatsapp_message(recipient, message)
        
        if success:
            return {"success": True, "message": f"Transmitted. I've sent that to {recipient} for you."}
        else:
            return {"success": False, "message": f"I couldn't complete the dispatch to {recipient}. Is the app open?"}
