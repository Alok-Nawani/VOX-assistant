import os
import requests
from typing import Dict, Optional
from datetime import datetime
import logging

class WeatherAPI:
    """Client for OpenWeatherMap API"""
    
    def __init__(self):
        """Initialize weather API client with API key from environment"""
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            logging.warning("OpenWeather API key not found in environment variables. Weather skill will be limited.")
            
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_current_weather(self, city: str) -> Optional[Dict]:
        """Get current weather for a city
        
        Args:
            city: Name of the city
            
        Returns:
            Dictionary containing weather data or None if request fails
        """
        if not self.api_key:
            return None

        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"  # Use metric units
            }
            
            response = requests.get(f"{self.base_url}/weather", params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"]
            }
            
        except Exception as e:
            logging.error(f"Error getting current weather: {e}")
            return None
            
    def get_forecast(self, city: str, days: int = 5) -> Optional[Dict]:
        """Get weather forecast for a city
        
        Args:
            city: Name of the city
            days: Number of days to forecast (max 5)
            
        Returns:
            Dictionary containing forecast data or None if request fails
        """
        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # API returns data in 3-hour intervals
            }
            
            response = requests.get(f"{self.base_url}/forecast", params=params)
            response.raise_for_status()
            
            data = response.json()
            daily_forecasts = {}
            
            for item in data["list"]:
                date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "description": item["weather"][0]["description"]
                    }
                else:
                    # Update min/max temperatures
                    daily_forecasts[date]["temp_min"] = min(
                        daily_forecasts[date]["temp_min"],
                        item["main"]["temp_min"]
                    )
                    daily_forecasts[date]["temp_max"] = max(
                        daily_forecasts[date]["temp_max"],
                        item["main"]["temp_max"]
                    )
                    
            return daily_forecasts
            
        except Exception as e:
            logging.error(f"Error getting weather forecast: {e}")
            return None
