from typing import Optional, Tuple
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from dataclasses import dataclass
import wave
import os
from datetime import datetime
import logging

@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    language: str
    timestamps: list[Tuple[float, float]]  # [(start_time, end_time), ...]

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio_buffer = []
        self.is_recording = False
        
    def _audio_callback(self, indata, frames, time, status):
        """Callback for sounddevice to capture audio"""
        if status:
            logging.warning(f"Audio input error: {status}")
        if self.is_recording:
            self.audio_buffer.append(indata.copy())
            
    def _detect_silence(self, audio_chunk: np.ndarray, threshold: float = 0.01, duration: float = 0.5) -> bool:
        """Detect if an audio chunk is silence"""
        chunk_duration = len(audio_chunk) / self.sample_rate
        if chunk_duration < duration:
            return False
            
        rms = np.sqrt(np.mean(np.square(audio_chunk)))
        return rms < threshold
        
    def record_until_silence(self, max_duration: float = 30.0, silence_duration: float = 1.0) -> Optional[np.ndarray]:
        """Record audio until silence is detected or max duration is reached"""
        self.audio_buffer = []
        self.is_recording = True
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self._audio_callback,
                dtype=np.float32
            ):
                total_recorded = 0
                silence_samples = 0
                
                while total_recorded < max_duration:
                    sd.sleep(100)  # Sleep for 100ms
                    total_recorded += 0.1
                    
                    if len(self.audio_buffer) > 0:
                        latest_chunk = np.concatenate(self.audio_buffer[-3:]) if len(self.audio_buffer) >= 3 else self.audio_buffer[-1]
                        
                        if self._detect_silence(latest_chunk):
                            silence_samples += 1
                            if (silence_samples / 10) >= silence_duration:  # Convert to seconds
                                break
                        else:
                            silence_samples = 0
                            
            self.is_recording = False
            
            if len(self.audio_buffer) == 0:
                return None
                
            # Combine all chunks
            return np.concatenate(self.audio_buffer)
            
        except Exception as e:
            logging.error(f"Recording error: {e}")
            self.is_recording = False
            return None
            
    def save_audio(self, audio_data: np.ndarray, filepath: str):
        """Save audio data to a WAV file"""
        try:
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        except Exception as e:
            logging.error(f"Error saving audio file: {e}")

class STTEngine:
    def __init__(self, model_size: str = "small"):
        """Initialize the STT engine with faster-whisper"""
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.recorder = AudioRecorder()
        
        # Create recordings directory if it doesn't exist
        os.makedirs("data/recordings", exist_ok=True)
        
    def transcribe_audio(self, audio_data: np.ndarray, save_recording: bool = True) -> Optional[TranscriptionResult]:
        """Transcribe audio data to text with metadata"""
        try:
            # Optionally save the recording
            if save_recording:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"data/recordings/recording_{timestamp}.wav"
                self.recorder.save_audio(audio_data, filepath)
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                language="en",
                vad_filter=True,
                word_timestamps=True
            )
            
            # Collect results
            text_parts = []
            timestamps = []
            
            for segment in segments:
                text_parts.append(segment.text)
                timestamps.append((segment.start, segment.end))
            
            if not text_parts:
                return None
                
            return TranscriptionResult(
                text=" ".join(text_parts).strip(),
                confidence=sum(s.avg_logprob for s in segments) / len(segments),
                language=info.language,
                timestamps=timestamps
            )
            
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return None
            
    def record_and_transcribe(self, max_duration: float = 30.0) -> Optional[TranscriptionResult]:
        """Record audio until silence and transcribe"""
        audio_data = self.recorder.record_until_silence(max_duration)
        if audio_data is None:
            return None
            
        return self.transcribe_audio(audio_data)

# Global STT instance
_engine = None

def transcribe_once(timeout: float = 30.0) -> Optional[str]:
    """Global function to record and transcribe audio once"""
    global _engine
    if _engine is None:
        _engine = STTEngine()
        
    result = _engine.record_and_transcribe(timeout)
    return result.text if result else None
