import time
import random
import asyncio
from datetime import datetime
from typing import Optional, Callable
from ..system.controller import SystemController
from ..tools.weather_api import WeatherAPI

class ProactiveEngine:
    """Engine that decides when Vox should initiate conversation"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.system = SystemController()
        
        self.last_interaction_time = time.time()
        self.last_proactive_time = time.time()
        self.working_session_start = time.time()
        self.is_running = False
        
        # State tracking for alerts
        self.alert_states = {
            "low_battery": False,
            "rain_notified": False
        }
        
        # Thresholds (30-90 minutes for casual nudges)
        self.casual_nudge_interval = random.randint(1800, 5400) 
        self.break_threshold = 7200 # 2 hours for work session nudge
        
    def notify_interaction(self):
        """Reset timers when the user speaks to Vox"""
        self.last_interaction_time = time.time()
        # Also push back proactive nudge to avoid interrupting fresh follow-ups
        self.last_proactive_time = time.time()
        
    async def run(self):
        """Background loop for checking proactive triggers"""
        self.is_running = True
        
        while self.is_running:
            await asyncio.sleep(60) # Deep check every minute
            
            now = time.time()
            current_hour = datetime.now().hour
            sys_status = self.system.get_system_status()
            
            # --- 1. CRITICAL SYSTEM ALERTS (Priority) ---
            if sys_status["battery_percent"] < 15 and not sys_status["is_charging"]:
                if not self.alert_states["low_battery"]:
                    await self.callback(f"Alok, your battery is at {sys_status['battery_percent']} percent. Might want to grab a charger.")
                    self.alert_states["low_battery"] = True
                    self.last_proactive_time = now
            elif sys_status["is_charging"] or sys_status["battery_percent"] > 20:
                self.alert_states["low_battery"] = False

            # --- 2. CASUAL & CONTEXTUAL PROACTIVITY ---
            # Don't speak if user was active in the last 15 minutes
            if now - self.last_interaction_time < 900:
                continue
                
            # Frequency Control (30-90 mins)
            if now - self.last_proactive_time < self.casual_nudge_interval:
                continue

            # Contextual Triggers
            msg = None
            
            # Late Night
            if current_hour >= 23 or current_hour < 2:
                msg = random.choice([
                    "It's getting late, Alok. Don't forget to rest.",
                    "Still at it? Make sure you don't burn the midnight oil too long.",
                    "Need anything before you call it a night?"
                ])
                
            # Long Work Session
            elif now - self.working_session_start > self.break_threshold:
                msg = random.choice([
                    "You've been at this a while. Want to take a quick break?",
                    "Looks like a long session today. Should I put on some music?",
                    "Taking a breather might help, Alok. Just a thought."
                ])
                self.working_session_start = now # Reset session timer
                
            # Inactive / Afternoon check
            elif 14 <= current_hour <= 16:
                msg = random.choice([
                    "Anything I can handle for you this afternoon?",
                    "How's the day going, Alok?",
                    "I'm here if you need any files organized or tasks handled."
                ])
            
            if msg:
                await self.callback(msg)
                self.last_proactive_time = now
                # Set a new random interval for the next nudge
                self.casual_nudge_interval = random.randint(1800, 5400)
                
    def stop(self):
        self.is_running = False
