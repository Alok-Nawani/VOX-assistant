from .base_skill import BaseSkill
from ..tools.weather_api import WeatherAPI
from typing import Dict, Any
import logging

class WeatherSkill(BaseSkill):
    """Skill for providing weather information"""
    
    def __init__(self):
        super().__init__("weather")
        self.weather_api = WeatherAPI()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "").lower()
        entities = params.get("entities", {})
        
        # Try to extract city from text if not in entities
        city = entities.get("location")
        if not city:
            # Simple heuristic: word after "in" or "at"
            import re
            match = re.search(r'(?:in|at|for|of)\s+([a-zA-Z\s]+)', text)
            if match:
                city = match.group(1).strip()
        
        if not city:
            return {"success": False, "message": "Which city should I check the weather for?"}
            
        try:
            weather = self.weather_api.get_current_weather(city)
            if not weather:
                return {"success": False, "message": f"Sorry, I couldn't find weather data for {city}."}
                
            msg = f"In {city}, it's currently {weather['description']} with a temperature of {weather['temperature']} degrees."
            return {
                "success": True,
                "message": msg,
                "data": weather
            }
        except Exception as e:
            logging.error(f"Weather skill error: {e}")
            return {"success": False, "message": "I had trouble reaching the weather service."}
