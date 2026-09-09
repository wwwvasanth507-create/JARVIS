"""
Voice Subsystem Orchestrator for JARVIS.
Integrates Audio Devices, VAD, STT, TTS, and Push-to-Talk with graceful error handling.
"""

from typing import Any, Dict, Generator, Optional
import logging
from jarvis.core.config import VoiceSettings
from jarvis.voice.audio_device import AudioDeviceDiscovery, AudioInputManager, AudioOutputManager
from jarvis.voice.vad import VoiceActivityDetector
from jarvis.voice.stt import SpeechRecognizer, LocalWhisperSTT, MockSpeechRecognizer
from jarvis.voice.tts import TextToSpeech, PyTTSx3TextToSpeech, MockTextToSpeech
from jarvis.voice.wakeword import WakeWordDetector, MockWakeWordDetector

logger = logging.getLogger("jarvis.voice.manager")


class VoiceManager:
    """Central Orchestrator for local speech recognition and synthesis."""

    def __init__(
        self,
        voice_settings: Optional[VoiceSettings] = None,
        stt: Optional[SpeechRecognizer] = None,
        tts: Optional[TextToSpeech] = None,
    ):
        self.settings = voice_settings or VoiceSettings()

        # Initialize STT engine
        if stt:
            self.stt = stt
        else:
            local_whisper = LocalWhisperSTT(self.settings.speech_to_text.model_dump())
            if local_whisper.is_available():
                self.stt = local_whisper
            else:
                logger.warning("LocalWhisperSTT dependencies unavailable, falling back to MockSpeechRecognizer")
                self.stt = MockSpeechRecognizer()

        # Initialize TTS engine
        if tts:
            self.tts = tts
        else:
            pyttsx3_tts = PyTTSx3TextToSpeech(self.settings.text_to_speech.model_dump())
            if pyttsx3_tts.is_available():
                self.tts = pyttsx3_tts
            else:
                logger.warning("PyTTSx3TextToSpeech unavailable, falling back to MockTextToSpeech")
                self.tts = MockTextToSpeech()

        # Audio devices & VAD
        self.audio_input = AudioInputManager(sample_rate=self.settings.audio.sample_rate)
        self.audio_output = AudioOutputManager()
        self.vad = VoiceActivityDetector(
            energy_threshold=self.settings.audio.vad_energy_threshold,
            silence_duration_seconds=self.settings.audio.vad_silence_duration,
        )

        # Wake-word detector preparation (PROMPT 004)
        self.wakeword = MockWakeWordDetector()

    def get_status(self) -> Dict[str, Any]:
        """Returns status summary of active voice components."""
        mic = AudioDeviceDiscovery.get_default_microphone()
        spk = AudioDeviceDiscovery.get_default_speaker()
        return {
            "enabled": self.settings.speech_to_text.enabled or self.settings.text_to_speech.enabled,
            "mode": self.settings.mode,
            "stt_available": self.stt.is_available(),
            "stt_engine": type(self.stt).__name__,
            "tts_available": self.tts.is_available(),
            "tts_engine": type(self.tts).__name__,
            "microphone": mic.name if mic else "None detected",
            "speaker": spk.name if spk else "None detected",
            "push_to_talk": self.settings.push_to_talk,
        }

    def listen_and_transcribe(self, duration_seconds: float = 3.0) -> str:
        """
        Records audio from microphone using push-to-talk/VAD, then transcribes via STT.
        Fails gracefully if microphone or STT is unavailable.
        """
        if not self.settings.speech_to_text.enabled:
            logger.info("Speech recognition is disabled in settings")
            return ""

        try:
            logger.info(f"VOICE_INPUT_STARTED: Capturing {duration_seconds}s of audio")
            pcm_bytes = self.audio_input.record_seconds(duration_seconds)
            
            if not pcm_bytes:
                logger.warning("No audio recorded or microphone unavailable")
                return ""

            # Energy VAD check to avoid transcribing pure silence
            if not self.vad.is_speech(pcm_bytes):
                logger.info("Audio below energy threshold (silence detected)")
                return ""

            text = self.stt.transcribe(pcm_bytes)
            return text.strip()
        except Exception as e:
            logger.error(f"VOICE_ERROR: Failed voice capture/transcription ({e})")
            return ""

    def speak(self, text: str) -> bool:
        """Synthesizes and plays text via TTS."""
        if not self.settings.text_to_speech.enabled or not text:
            return False

        try:
            return self.tts.speak(text)
        except Exception as e:
            logger.error(f"VOICE_ERROR: TTS output failed ({e}) - continuing in text mode")
            return False

    def speak_stream(self, token_generator: Generator[str, None, Any]) -> str:
        """Synthesizes text in sentence chunks progressively while tokens stream from LLM."""
        if not self.settings.text_to_speech.enabled:
            return "".join(list(token_generator))

        if hasattr(self.tts, "speak_stream"):
            return self.tts.speak_stream(token_generator)
        else:
            text = "".join(list(token_generator))
            self.speak(text)
            return text

    def stop_speech(self) -> None:
        """Stops active speech immediately."""
        self.tts.stop()
        self.audio_output.stop()
