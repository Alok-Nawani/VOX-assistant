import os
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Optional

class IntentParser:
    """Uses Gemini to parse natural language into structured actionable steps."""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.warning("No GEMINI_API_KEY found. Intent Parser will fall back to simple matching.")
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
        
    async def parse(self, text: str, aliases: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Parses text into a list of actions.
        Returns: [{"skill": "skill_name", "query": "specific action"}]
        """
        if not text.strip():
            return []
            
        # First, check aliases (Command Learning)
        if aliases:
            text_lower = text.lower().strip()
            # Basic fuzzy matching for aliases
            for alias_key, alias_val in aliases.items():
                if alias_key in text_lower:
                    text = text_lower.replace(alias_key, alias_val)
                    logging.info(f"Alias matched! Executing underlying command: {text}")
                    break

        if not self.model:
            return [{"skill": "conversation", "query": text}]

        prompt = f"""You are the routing brain of VOX. Parse the user's input into a JSON array of steps.
Available Skills:
1. system_control: Use for opening apps, taking screenshots, volume, or brightness.
2. media: Use for playing songs, music, or controlling playback.
3. whatsapp: Use for sending messages to contacts.
4. art: Use for generating images or drawing.
5. conversation: Use for greetings (hi, hello) or general questions.

Example 1: "Open calculator" -> {{"steps": [{{"skill": "system_control", "query": "calculator"}}]}}
Example 2: "Play some music" -> {{"steps": [{{"skill": "media", "query": "music"}}]}}
Example 3: "Hi Vox" -> {{"steps": [{{"skill": "conversation", "query": "Hi Vox"}}]}}

Return ONLY valid JSON.
User Input: "{text}" """
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up markdown if model outputs it
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
                
            parsed = json.loads(result_text)
            return parsed.get("steps", [{"skill": "conversation", "query": text}])
        except Exception as e:
            logging.error(f"Intent Parser failed: {e}")
            # Fallback
            return [{"skill": "conversation", "query": text}]
