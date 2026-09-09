"""
Speech-to-Text (STT) Local Inference Abstraction for JARVIS.
Provides local CPU-first speech recognition without cloud API dependencies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import time

logger = logging.getLogger("jarvis.voice.stt")


class SpeechRecognizer(ABC):
    """Abstract Base Class for all Speech-to-Text recognizers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribes raw PCM audio data into text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine dependencies and model are ready."""
        pass


class MockSpeechRecognizer(SpeechRecognizer):
    """Mock STT Provider for unit tests and headless execution."""

    def __init__(self, mock_transcript: str = "Hello JARVIS", config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.mock_transcript = mock_transcript

    def is_available(self) -> bool:
        return True

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        logger.info("STT_STARTED (Mock)")
        time.sleep(0.05)
        logger.info(f"STT_COMPLETED (Mock): '{self.mock_transcript}'")
        return self.mock_transcript


class LocalWhisperSTT(SpeechRecognizer):
    """
    Local Whisper STT Engine using faster-whisper or openai-whisper on CPU.
    Supports auto-language detection including English, Tamil, and Tamil-English code-switching.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_size = self.config.get("model", "tiny")
        self.device = self.config.get("device", "cpu")
        self.compute_type = self.config.get("compute_type", "int8")
        self.language = self.config.get("language", "auto")
        self._model = None

    def is_available(self) -> bool:
        try:
            import faster_whisper
            return True
        except ImportError:
            try:
                import whisper
                return True
            except ImportError:
                return False

    def initialize(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            lang = None if self.language == "auto" else self.language
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
            )
            logger.info(f"Initialized faster-whisper model '{self.model_size}' on CPU")
        except Exception as e:
            logger.warning(f"faster-whisper init failed ({e}), falling back to openai-whisper if present")
            import whisper
            self._model = whisper.load_model(self.model_size, device=self.device)

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        if not audio_data:
            return ""

        logger.info("STT_STARTED")
        start_time = time.perf_counter()

        try:
            self.initialize()
            import numpy as np

            # Convert 16-bit PCM bytes to float32 normalized numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            if hasattr(self._model, "transcribe"):
                # Check if faster-whisper signature
                if type(self._model).__name__ == "WhisperModel":
                    lang_param = None if self.language == "auto" else self.language
                    segments, info = self._model.transcribe(
                        audio_array, language=lang_param, beam_size=1
                    )
                    text = " ".join([seg.text.strip() for seg in segments])
                else:
                    # openai-whisper fallback
                    res = self._model.transcribe(audio_array, fp16=False)
                    text = res.get("text", "").strip()
            else:
                text = ""

            duration = time.perf_counter() - start_time
            logger.info(f"STT_COMPLETED: '{text}' (took {duration:.2f}s)")
            return text
        except Exception as e:
            logger.error(f"VOICE_ERROR: STT transcription failed ({e})")
            return ""


class SpeechRecognitionSTT(SpeechRecognizer):
    """
    STT Engine leveraging Python SpeechRecognition package (Sphinx / Google Web fallback if offline fails).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    def is_available(self) -> bool:
        try:
            import speech_recognition as sr
            return True
        except ImportError:
            return False

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        if not audio_data:
            return ""

        logger.info("STT_STARTED (SpeechRecognition)")
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            audio_file = sr.AudioData(audio_data, sample_rate, 2)
            
            # Try offline Sphinx first if installed, else handle exception
            try:
                text = recognizer.recognize_sphinx(audio_file)
            except Exception:
                # If sphinx not installed/fails, log and return empty for fallback
                logger.warning("Sphinx offline recognition unavailable")
                text = ""

            logger.info(f"STT_COMPLETED: '{text}'")
            return text
        except Exception as e:
            logger.error(f"VOICE_ERROR: SpeechRecognition STT failed ({e})")
            return ""
