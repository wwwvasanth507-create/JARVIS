"""
Text-to-Speech (TTS) Local Synthesis Abstraction for JARVIS.
Provides local CPU synthesis configured for a natural female voice (e.g., Microsoft Zira Desktop).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
import logging
import re
import time

logger = logging.getLogger("jarvis.voice.tts")


class TextToSpeech(ABC):
    """Abstract Base Class for all Text-to-Speech engines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def speak(self, text: str) -> bool:
        """Synthesizes and speaks text to audio output."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops ongoing speech playback immediately."""
        pass

    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns metadata for available system voices."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if engine dependencies are available."""
        pass


class MockTextToSpeech(TextToSpeech):
    """Mock TTS Provider for unit testing and headless execution."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._is_speaking = False

    def is_available(self) -> bool:
        return True

    def speak(self, text: str) -> bool:
        if not text:
            return False
        logger.info(f"TTS_STARTED (Mock): '{text}'")
        self._is_speaking = True
        time.sleep(0.05)
        self._is_speaking = False
        logger.info("TTS_COMPLETED (Mock)")
        return True

    def stop(self) -> None:
        if self._is_speaking:
            self._is_speaking = False
            logger.info("TTS_STOPPED (Mock)")

    def get_available_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "mock_zira", "name": "Mock Female JARVIS Voice", "gender": "Female", "language": "en_US"}
        ]


class PyTTSx3TextToSpeech(TextToSpeech):
    """
    Local Text-to-Speech Engine using pyttsx3 (SAPI5 on Windows).
    Discovers native female voices (e.g. Microsoft Zira Desktop, Microsoft Hazel Desktop).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.preferred_voice = self.config.get("voice", "auto")
        self.speed = float(self.config.get("speed", 1.0))
        self.volume = float(self.config.get("volume", 1.0))
        self._engine = None
        self._is_speaking = False

    def is_available(self) -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def _init_engine(self) -> None:
        if self._engine is not None:
            return
        import pyttsx3

        self._engine = pyttsx3.init()
        
        # Configure female voice
        voices = self._engine.getProperty("voices")
        selected_voice = None

        if self.preferred_voice != "auto":
            for v in voices:
                if self.preferred_voice.lower() in v.id.lower() or self.preferred_voice.lower() in v.name.lower():
                    selected_voice = v
                    break

        if not selected_voice:
            # Look for female voice keywords: Zira, Hazel, Female
            for v in voices:
                name_lower = v.name.lower()
                gender_attr = getattr(v, "gender", "")
                if "zira" in name_lower or "hazel" in name_lower or "female" in str(gender_attr).lower():
                    selected_voice = v
                    break

        if selected_voice:
            self._engine.setProperty("voice", selected_voice.id)
            logger.info(f"Selected female TTS voice: '{selected_voice.name}'")

        # Set speed & volume
        current_rate = self._engine.getProperty("rate")
        self._engine.setProperty("rate", int(current_rate * self.speed))
        self._engine.setProperty("volume", self.volume)

    def speak(self, text: str) -> bool:
        if not text:
            return False
        logger.info(f"TTS_STARTED: '{text[:40]}...'")
        self._is_speaking = True
        try:
            self._init_engine()
            self._engine.say(text)
            self._engine.runAndWait()
            self._is_speaking = False
            logger.info("TTS_COMPLETED")
            return True
        except Exception as e:
            self._is_speaking = False
            logger.error(f"VOICE_ERROR: TTS synthesis failed ({e})")
            return False

    def speak_stream(self, token_generator: Generator[str, None, Any]) -> str:
        """
        Sentence-level streaming TTS. As tokens arrive, complete sentences are spoken
        immediately while subsequent tokens continue generating.
        """
        logger.info("TTS_STREAM_STARTED")
        buffer = []
        full_text = []

        # Sentence end regex: . ! ? or newline
        sentence_end_pattern = re.compile(r"([.!?\n]+)")

        for token in token_generator:
            buffer.append(token)
            full_text.append(token)
            current_str = "".join(buffer)

            match = sentence_end_pattern.search(current_str)
            if match:
                end_idx = match.end()
                sentence_to_speak = current_str[:end_idx].strip()
                buffer = [current_str[end_idx:]]
                if sentence_to_speak:
                    self.speak(sentence_to_speak)

        # Speak remaining buffer text
        remaining = "".join(buffer).strip()
        if remaining:
            self.speak(remaining)

        return "".join(full_text)

    def stop(self) -> None:
        if self._engine and self._is_speaking:
            try:
                self._engine.stop()
            except Exception:
                pass
            self._is_speaking = False
            logger.info("TTS_STOPPED")

    def get_available_voices(self) -> List[Dict[str, Any]]:
        try:
            self._init_engine()
            voices = self._engine.getProperty("voices")
            return [
                {
                    "id": v.id,
                    "name": v.name,
                    "gender": getattr(v, "gender", "Unknown"),
                    "languages": getattr(v, "languages", []),
                }
                for v in voices
            ]
        except Exception as e:
            logger.warning(f"Failed to query pyttsx3 voices ({e})")
            return []
