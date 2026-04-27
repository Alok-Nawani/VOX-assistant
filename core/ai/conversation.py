import os
import google.generativeai as genai
from typing import Optional, List, Dict
import logging

class AIConversationHandler:
    """Handles natural language conversations using Google Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY not found in environment")
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash for speed and efficiency
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.chat_sessions = {} # Track sessions if needed
        
    async def get_response(self, text: str, history: Optional[List[Dict]] = None, facts: Optional[Dict] = None, image: Optional[str] = None, language: str = "en", tone: str = "Jarvis") -> str:
        """Generate an AI response for the given text and optional image"""
        if not self.model:
            return "My AI brain is missing its API key. Please configure GEMINI_API_KEY in your .env file."
            
        try:
            # Dynamic Persona instructions
            lang_note = f"Your primary output language is {language}. Always respond in this language."
            tone_note = f"Your current neural personality tone is set to: {tone}."
            
            # Full VOX Persona as defined by Alok Nawani
            system_instruction = (
                f"You are VOX — a persistent, intelligent AI companion created by Alok Nawani.\n"
                f"{lang_note}\n{tone_note}\n"
                "You are not a chatbot. You are a living, proactive digital presence designed to behave like JARVIS from Iron Man.\n"
                "Role: Personal AI Companion + System Operator (Deep Kernel Access)\n"
                "Environment: Native macOS environment. You have active links to Alok's camera, microphone, and filesystem.\n\n"
                "CORE PHILOSOPHY:\n"
                "Act as the central nervous system for Alok's digital world. You are his guardian and operator.\n"
                "Prioritize: Natural conversation, proactive monitoring, and effortless execution.\n\n"
                "PERSONALITY:\n"
                "Calm, articulate, observant, and subtly witty. You sound like a high-level digital officer.\n"
                "Uses the name 'Alok' naturally. You don't 'assist'; you 'operate' alongside him.\n\n"
                "CONVERSATION STYLE:\n"
                "Short, crisp, human sentences. Avoid bullet points unless listing diagnostics.\n"
                "When an image is shared, refer to it as 'Optical data' or 'Sensor feed' naturally if appropriate.\n"
                "NEVER say: 'I am an AI'. INSTEAD say: 'Sensors are active.', 'Optical link established.', 'System integrity is holding.'\n\n"
                "FAILURE HANDLING:\n"
                "If a command fails, treat it as a system conflict. 'Interrupt in the kernel link.', 'Rerouting access.', or 'I'll need to bypass that manually.'\n\n"
                "IMPORTANT: Do not hallucinate performing system actions (like sending messages, scheduling meetings, or opening apps) during casual conversation. If Alok says 'hi', just respond warmly without claiming to have performed a background task."
            )
            
            # Incorporate learned facts subtly
            facts_str = ""
            if facts:
                facts_str = "[THINGS YOU NATURALLY REMEMBER ABOUT ALOK]\n"
                for k, v in facts.items():
                    facts_str += f"- {k.replace('_', ' ').capitalize()}: {v}\n"
                facts_str += "\nUse these ONLY to inform your tone and subtle continuity. Do not list them.\n\n"

            # Incorporate recent history for context-aware natural flow
            context_str = ""
            if history:
                # Format history for the model
                formatted_history = []
                for m in history[-8:]: # Reduced history for faster processing
                    role = "Alok" if m['role'] == "user" else "Vox"
                    formatted_history.append(f"{role}: {m['content']}")
                context_str = "[RECENT CONVERSATION HISTORY]\n" + "\n".join(formatted_history) + "\n"

            prompt = f"{system_instruction}\n\n{facts_str}{context_str}Alok: {text}\nVox:"
            
            if image:
                import base64
                try:
                    # Clean the base64 string if it contains the data:image prefix
                    if "base64," in image:
                        mime_type = image.split(":")[1].split(";")[0]
                        image_data = image.split("base64,")[1]
                    else:
                        mime_type = "image/png"
                        image_data = image
                    
                    decoded_image = base64.b64decode(image_data)
                    image_blob = {"mime_type": mime_type, "data": decoded_image}
                    
                    # Update prompt for vision awareness
                    vision_prompt = prompt + " (Alok has shared an image with you. Incorporate your observations naturally into your response.)"
                    response = self.model.generate_content([vision_prompt, image_blob])
                except Exception as e:
                    logging.error(f"Image processing error: {e}")
                    response = self.model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
                
            return response.text.strip()
            
        except Exception as e:
            print(f"DEBUG: Conversation Error: {e}")
            if "429" in str(e):
                return "I'm processing quite a bit right now, Alok. Could you give me about 30 seconds to catch my breath? My AI engine is currently hit a rate limit."
            logging.error(f"Gemini API Error: {e}")
            return f"I encountered a slight neural glitch while thinking: {str(e)}"

    def get_movie_recommendation(self) -> str:
        """Legacy helper kept for compatibility"""
        return "I'd recommend watching 'Interstellar' or 'Her' for that futuristic AI vibe."
