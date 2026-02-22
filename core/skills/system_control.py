from .base_skill import BaseSkill
from ..system.controller import SystemController
from typing import Dict, Any

class SystemControlSkill(BaseSkill):
    """Skill for managing macOS system operations"""
    
    def __init__(self):
        super().__init__("system_control")
        self.controller = SystemController()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        intent = params.get("intent", "").lower()
        entities = params.get("entities", {})
        text = params.get("raw_text", "").lower()
        
        # Determine specific action
        if "volume" in text or intent == "volume_set":
            volume = self._extract_volume(text)
            success, _ = self.controller.control_volume("set", volume)
            if success:
                return {"success": True, "message": f"Alright, volume's at {volume} percent now."}
            return {"success": False, "message": "Sorry, I couldn't change the volume."}
            
        # Handle app opening
        if any(cmd in text for cmd in ["open", "launch", "start"]):
            app_name = self._extract_app_name(text, ["open", "launch", "start"])
            if app_name:
                success, _ = self.controller.open_app(app_name)
                if success:
                    return {"success": True, "message": f"Opening {app_name}. Ready when you are."}
                return {"success": False, "message": f"I tried, but I couldn't open {app_name}."}
            return {"success": False, "message": "Which app did you want me to open?"}

        # Handle app closing
        if any(cmd in text for cmd in ["close", "quit", "stop"]):
            app_name = self._extract_app_name(text, ["close", "quit", "stop"])
            if app_name:
                success, _ = self.controller.close_app(app_name)
                if success:
                    return {"success": True, "message": f"Done. Closed {app_name}."}
                return {"success": False, "message": f"I couldn't close {app_name} for some reason."}
            return {"success": False, "message": "Which app should I close?"}

        # Handle brightness/dimming
        if any(cmd in text for cmd in ["dim", "brightness", "screen"]):
            level = 20 if "dim" in text else 70
            if "max" in text: level = 100
            elif "half" in text: level = 50
            
            # Try to extract a specific number if present
            import re
            match = re.search(r'(\d+)', text)
            if match: level = int(match.group(1))

            success, _ = self.controller.set_brightness(level)
            if success:
                return {"success": True, "message": f"Done. Your brightness is at {level} percent."}
            return {"success": False, "message": "I couldn't adjust the display brightness."}

        elif any(cmd in text for cmd in ["click my picture", "take a photo", "take my picture", "capture image"]):
            return {
                "success": True, 
                "message": "Initiating optical capture. 3... 2... 1... cheese!",
                "data": {"action": "camera_capture", "countdown": 3}
            }
        elif "screenshot" in text:
            success, _ = self.controller.take_screenshot()
            return {"success": success, "message": "Screenshot's on your desktop, Alok." if success else "I couldn't take that screenshot."}
        elif any(cmd in text for cmd in ["sleep", "lock"]):
            action = "sleep" if "sleep" in text else "lock"
            success, msg = self.controller.system_power(action)
            return {"success": success, "message": msg}
        elif any(word in text for word in ["battery", "power"]):
            stats = self.controller.get_system_stats()
            level = stats.get("battery", 0)
            return {"success": True, "message": f"Your battery level is currently at {level:.1f} percent, Alok."}
        elif any(word in text for word in ["cpu", "ram", "memory", "stats"]):
            stats = self.controller.get_system_stats()
            return {"success": True, "message": f"System status: CPU is at {stats.get('cpu', 0):.1f}%, and Memory is at {stats.get('ram', 0):.1f}%."}
            
        return {"success": False, "message": "I'm not sure which system command to run."}

    def _extract_volume(self, text: str) -> int:
        import re
        if "mute" in text: return 0
        if "max" in text: return 100
        match = re.search(r'(\d+)', text)
        if match: return int(match.group(1))
        if "up" in text: return 70
        if "down" in text: return 30
        return 50

    def _extract_app_name(self, text: str, triggers: list) -> str:
        words = text.split()
        for i, word in enumerate(words):
            if word in triggers:
                if i + 1 < len(words):
                    return " ".join(words[i+1:])
        return ""

# For backward compatibility if needed by old brain.py
def run(payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio
    skill = SystemControlSkill()
    # Payload has "text", execute expects "raw_text"
    params = {"raw_text": payload.get("text", "")}
    # This is a sync wrapper for an async call - not ideal but works for migration
    return asyncio.run(skill.execute(params))
