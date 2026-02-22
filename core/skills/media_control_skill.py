from typing import Dict, Optional, Any
from .base_skill import BaseSkill
from ..tools.media_controller import MediaController
import logging

class MediaControlSkill(BaseSkill):
    """Skill for controlling media playback"""
    
    def __init__(self):
        super().__init__("media_control")
        self.media_controller = MediaController()
        
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params.get("raw_text", "").lower()
        history = params.get("history", [])
        
        # 1. Deterministic Extraction (AI Fallback)
        import re
        def get_fallback_info(t):
            t = t.lower().strip()
            # Pattern: play [Query]
            if any(cmd in t for cmd in ["play", "start", "listen to"]):
                # Split at 'play' and take everything after
                for cmd in ["play", "start music", "listen to"]:
                    if cmd in t:
                        query = t.split(cmd)[-1].strip()
                        return "play", query
            
            if any(cmd in t for cmd in ["pause", "stop"]): return "pause", None
            if any(cmd in t for cmd in ["resume", "continue"]): return "resume", None
            if any(cmd in t for cmd in ["next", "skip"]): return "next", None
            if any(cmd in t for cmd in ["previous", "back"]): return "previous", None
            
            return None, None

        # Try to determine action/query
        action, query = get_fallback_info(text)
        
        # If AI is available and we didn't get a clear hit, we'd normally use AI here.
        # But for media, regex is very reliable.
        
        try:
            if action == "play":
                return await self._handle_play(text, {"query": query})
            elif action == "pause":
                return await self._handle_pause()
            elif action == "resume":
                return await self._handle_resume()
            elif action == "next":
                return await self._handle_next()
            elif action == "previous":
                return await self._handle_previous()
            
            return {"success": False, "message": "I'm not sure what you want me to do with the music, Alok."}
        except Exception as e:
            logging.error(f"Media skill error: {e}")
            return {"success": False, "message": "I encountered an issue while controlling your music."}

    async def _handle_play(self, text: str, entities: Dict) -> Dict[str, Any]:
        query = entities.get("query") or text.split("play")[-1].strip()
        if not query or query in ["music", "something"]:
            await self.media_controller.resume()
            return {"success": True, "message": "Alright, resuming your music."}
            
        success = await self.media_controller.play_media(query)
        if success:
            return {"success": True, "message": f"Got it. Playing {query} for you."}
        return {"success": False, "message": f"I couldn't find {query} to play."}

    async def _handle_pause(self) -> Dict[str, Any]:
        await self.media_controller.pause()
        return {"success": True, "message": "Music's paused."}

    async def _handle_resume(self) -> Dict[str, Any]:
        await self.media_controller.resume()
        return {"success": True, "message": "Continuing the tunes."}

    async def _handle_next(self) -> Dict[str, Any]:
        await self.media_controller.next_track()
        return {"success": True, "message": "Skipping to the next one."}

    async def _handle_previous(self) -> Dict[str, Any]:
        await self.media_controller.previous_track()
        return {"success": True, "message": "Going back a track."}
