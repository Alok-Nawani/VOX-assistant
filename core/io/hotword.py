import time
from typing import Optional
import openwakeword
import sounddevice as sd
import numpy as np

class HotwordDetector:
    def __init__(self):
        """Initialize the hotword detector with OpenWakeWord (with manual fallback)"""
        try:
            # Using 'hey_jarvis' as a proxy for Vox due to pre-trained model availability
            self.detector = openwakeword.Model(wakeword_models=["hey_jarvis"])
            print("Vox Voice Trigger: Ready (Hey Jarvis)")
        except Exception as e:
            print(f"Warning: Hotword engine failed to load ({e}). Falling back to manual trigger.")
            print(">>> PRESS ENTER to talk to VOX <<<")
            self.detector = None
            
        self.sample_rate = 16000
        self.running = False
        self.detected_word = None
        
    def audio_callback(self, indata, frames, time, status):
        """Process audio chunks from the microphone"""
        if status:
            print(f"Audio callback error: {status}")
            return
            
        # Process the audio chunk with the detector
        audio_chunk = np.frombuffer(indata, dtype=np.float32)
        self.detector.predict(audio_chunk)
        
        # Check scores
        scores = self.detector.get_predictions()
        
        if scores["hey_jarvis"] > 0.5:
            self.detected_word = "hey_vox"
            self.running = False
            
    def wait_for_hotword(self) -> Optional[str]:
        """Listen for the wake word and block until detected"""
        if self.detector is None:
            # Manual fallback
            input("")
            return "hey_vox"

        self.running = True
        self.detected_word = None
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=1024
            ):
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Warning: Could not access microphone ({e}). Using manual trigger.")
            input(">>> Press Enter to talk <<<")
            return "hey_vox"
        
        return self.detected_word

# Global detector instance
_detector = None

def init_detector():
    """Explicitly initialize the global detector"""
    global _detector
    if _detector is None:
        _detector = HotwordDetector()
    return _detector

def wait_for_hotword() -> Optional[str]:
    """Global function to wait for hotword detection"""
    global _detector
    if _detector is None:
        init_detector()
    return _detector.wait_for_hotword()
