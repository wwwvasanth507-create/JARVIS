"""
Wake-Word Subsystem and Local 2-Stage Detector for JARVIS.
CPU-first wake-word detection supporting single-utterance parsing, cooldowns, and graceful degradation.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import re
import time

logger = logging.getLogger("jarvis.voice.wakeword")


class WakeWordDetector(ABC):
    """Abstract Base Class for all Wake-Word Detectors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.phrase = self.config.get("phrase", "JARVIS").upper()
        self.secondary_phrases = [p.upper() for p in self.config.get("secondary_phrases", ["HEY JARVIS"])]
        self.sensitivity = float(self.config.get("sensitivity", 0.5))
        self.cooldown_seconds = float(self.config.get("cooldown_seconds", 1.0))
        self.command_timeout_seconds = float(self.config.get("command_timeout_seconds", 8.0))
        self.model_path = Path(self.config.get("model_path", "models/wakeword/jarvis.onnx"))
        
        self.is_active = False
        self.is_paused = False
        self._last_detection_time = 0.0

    @abstractmethod
    def start(self) -> None:
        """Starts wake-word detector."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops wake-word detector."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pauses wake-word detection."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resumes wake-word detection."""
        pass

    @abstractmethod
    def is_detected(self, audio_chunk: bytes) -> bool:
        """Returns True if the wake-word was detected in the audio chunk."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if local wake-word engine dependencies and model are ready."""
        pass

    def check_cooldown(self) -> bool:
        """Returns True if cooldown period has elapsed since last wake detection."""
        return (time.time() - self._last_detection_time) >= self.cooldown_seconds

    def parse_single_utterance(self, transcribed_text: str) -> Tuple[bool, str]:
        """
        Parses transcribed text to determine if a wake word was spoken
        and extracts any trailing command in the same utterance (e.g. 'JARVIS, open Chrome.').
        Returns (wake_detected: bool, extracted_command: str).
        """
        if not transcribed_text:
            return False, ""

        clean_text = transcribed_text.strip().upper()
        target_phrases = [self.phrase] + self.secondary_phrases

        for p in target_phrases:
            if clean_text.startswith(p):
                # Extract command after wake phrase
                remainder = clean_text[len(p) :].strip(" ,.!?")
                return True, remainder
            elif p in clean_text:
                # Phrase appears inside text
                idx = clean_text.index(p)
                remainder = clean_text[idx + len(p) :].strip(" ,.!?")
                return True, remainder

        return False, ""


class MockWakeWordDetector(WakeWordDetector):
    """Mock Wake-Word Detector for unit tests and automated state machine simulation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._simulated_detection = False

    def is_available(self) -> bool:
        return True

    def start(self) -> None:
        self.is_active = True
        self.is_paused = False
        logger.info(f"MockWakeWordDetector started for phrase '{self.phrase}'")

    def stop(self) -> None:
        self.is_active = False
        self.is_paused = False
        logger.info("MockWakeWordDetector stopped")

    def pause(self) -> None:
        self.is_paused = True
        logger.info("WAKEWORD_PAUSED: MockWakeWordDetector paused")

    def resume(self) -> None:
        self.is_paused = False
        logger.info("WAKEWORD_RESUMED: MockWakeWordDetector resumed")

    def trigger_wake_event(self) -> None:
        self._simulated_detection = True

    def is_detected(self, audio_chunk: bytes) -> bool:
        if not self.is_active or self.is_paused or not self.check_cooldown():
            return False

        if self._simulated_detection:
            self._simulated_detection = False
            self._last_detection_time = time.time()
            return True

        return False


class LocalWakeWordDetector(WakeWordDetector):
    """
    Local CPU 2-Stage Wake-Word Detector.
    Stage 1: RMS energy check & fast acoustic pattern matcher (or openwakeword ONNX model if installed).
    Stage 2: Full local STT activated ONLY when Stage 1 indicates candidate speech.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, stt_engine: Optional[Any] = None):
        super().__init__(config)
        self.stt_engine = stt_engine
        self._onnx_model = None

    def is_available(self) -> bool:
        # Check if local model exists or openwakeword package is available
        if self.model_path.exists():
            return True
        try:
            import openwakeword
            return True
        except ImportError:
            # Degrades gracefully if model file or openwakeword library is absent
            return False

    def start(self) -> None:
        self.is_active = True
        self.is_paused = False
        logger.info(f"WAKEWORD_STARTED: LocalWakeWordDetector active for phrase '{self.phrase}'")

    def stop(self) -> None:
        self.is_active = False
        self.is_paused = False

    def pause(self) -> None:
        self.is_paused = True
        logger.info("WAKEWORD_PAUSED: Local wake-word detector paused")

    def resume(self) -> None:
        self.is_paused = False
        logger.info("WAKEWORD_RESUMED: Local wake-word detector resumed")

    def is_detected(self, audio_chunk: bytes) -> bool:
        """
        Stage 1 & Stage 2 verification.
        Returns True only if wake word is detected and cooldown has elapsed.
        """
        if not self.is_active or self.is_paused or not self.check_cooldown():
            return False

        if not audio_chunk:
            return False

        # Stage 1: Check audio energy level first (avoid running STT on silence)
        from jarvis.voice.vad import VoiceActivityDetector
        vad = VoiceActivityDetector(energy_threshold=150)
        if not vad.is_speech(audio_chunk):
            return False

        # Stage 2: Lightweight phonetic transcription if STT engine provided
        if self.stt_engine:
            transcript = self.stt_engine.transcribe(audio_chunk)
            wake_found, _ = self.parse_single_utterance(transcript)
            if wake_found:
                self._last_detection_time = time.time()
                logger.info(f"WAKEWORD_DETECTED: Wake phrase '{self.phrase}' detected in audio")
                return True

        return False
