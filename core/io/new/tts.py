import os
import queue
import threading
import pyttsx3
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class TTSProvider(Enum):
    SYSTEM = "system"
    PYTTSX3 = "pyttsx3"
    ELEVENLABS = "elevenlabs"

@dataclass
class TTSRequest:
    text: str
    voice: str = "default"
    priority: int = 1
    interrupt_current: bool = False

class TTSEngine:
    def __init__(self):
        """Initialize TTS with a message queue and background worker"""
        self.message_queue = queue.PriorityQueue()
        self.current_speaking = threading.Event()
        self.should_stop = threading.Event()
        self.provider = TTSProvider.SYSTEM
        
        # Initialize offline TTS
        self.pyttsx3_engine = pyttsx3.init()
        self.pyttsx3_engine.setProperty('rate', 175)
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
    def _process_queue(self):
        """Background worker to process TTS requests"""
        while not self.should_stop.is_set():
            try:
                # Get next message from queue
                _, request = self.message_queue.get(timeout=0.1)
                
                # Set speaking flag and speak
                self.current_speaking.set()
                self._speak_text(request.text)
                self.current_speaking.clear()
                
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"TTS error: {e}")
                self.current_speaking.clear()
                
    def _speak_text(self, text: str):
        """Actually speak the text using selected provider"""
        if self.provider == TTSProvider.SYSTEM:
            if os.name == "posix":  # macOS/Linux
                os.system(f'say "{text}"')
            else:  # Windows
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
        elif self.provider == TTSProvider.PYTTSX3:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
        elif self.provider == TTSProvider.ELEVENLABS:
            # Implement ElevenLabs integration if API key available
            pass
            
    def speak(self, text: str, interrupt: bool = False):
        """Add text to the speaking queue"""
        if interrupt and self.current_speaking.is_set():
            self.stop_speaking()
            
        request = TTSRequest(
            text=text,
            priority=0 if interrupt else 1,
            interrupt_current=interrupt
        )
        self.message_queue.put((request.priority, request))
        
    def stop_speaking(self):
        """Stop current speech and clear queue"""
        if self.provider == TTSProvider.SYSTEM:
            if os.name == "posix":
                os.system("killall say")
        elif self.provider == TTSProvider.PYTTSX3:
            self.pyttsx3_engine.stop()
            
        # Clear queue
        with self.message_queue.mutex:
            self.message_queue.queue.clear()
        self.current_speaking.clear()
        
    def cleanup(self):
        """Clean up resources"""
        self.should_stop.set()
        self.stop_speaking()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)

# Global TTS instance
_engine = None

def speak(text: str, interrupt: bool = False):
    """Global function to speak text"""
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    _engine.speak(text, interrupt)

def stop_speaking():
    """Global function to stop speaking"""
    global _engine
    if _engine is not None:
        _engine.stop_speaking()
