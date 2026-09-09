"""
Voice Subsystem Orchestrator for JARVIS.
Integrates VoiceStateMachine, AudioOwnershipManager, WakeWordDetector, STT, TTS,
Fast-Path Acknowledgement, Single-Utterance Parsing, and Speech Interruption.
"""

from typing import Any, Dict, Generator, Optional, Tuple
import logging
import time

from jarvis.core.config import VoiceSettings, WakeWordSettings
from jarvis.voice.audio_device import AudioDeviceDiscovery, AudioInputManager, AudioOutputManager
from jarvis.voice.vad import VoiceActivityDetector
from jarvis.voice.stt import SpeechRecognizer, LocalWhisperSTT, MockSpeechRecognizer
from jarvis.voice.tts import TextToSpeech, PyTTSx3TextToSpeech, MockTextToSpeech
from jarvis.voice.wakeword import WakeWordDetector, LocalWakeWordDetector, MockWakeWordDetector
from jarvis.voice.state_machine import VoiceStateMachine, MicrophoneState
from jarvis.voice.ownership import AudioOwnershipManager

logger = logging.getLogger("jarvis.voice.manager")


class VoiceManager:
    """Central Orchestrator for local speech recognition, wake-word detection, and TTS synthesis."""

    def __init__(
        self,
        voice_settings: Optional[VoiceSettings] = None,
        wakeword_settings: Optional[WakeWordSettings] = None,
        stt: Optional[SpeechRecognizer] = None,
        tts: Optional[TextToSpeech] = None,
        wakeword: Optional[WakeWordDetector] = None,
    ):
        self.settings = voice_settings or VoiceSettings()
        self.wakeword_settings = wakeword_settings or WakeWordSettings()

        # State Machine & Audio Ownership
        self.state_machine = VoiceStateMachine(initial_state=MicrophoneState.MICROPHONE_OFF)
        self.ownership = AudioOwnershipManager()

        # Initialize STT engine
        if stt:
            self.stt = stt
        else:
            local_whisper = LocalWhisperSTT(self.settings.speech_to_text.model_dump())
            if local_whisper.is_available():
                self.stt = local_whisper
            else:
                logger.warning("LocalWhisperSTT unavailable, falling back to MockSpeechRecognizer")
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

        # Initialize Wake-Word detector
        if wakeword:
            self.wakeword = wakeword
        else:
            local_ww = LocalWakeWordDetector(self.wakeword_settings.model_dump(), stt_engine=self.stt)
            if local_ww.is_available():
                self.wakeword = local_ww
            else:
                logger.warning("Local wake-word model/engine unavailable. Falling back to MockWakeWordDetector.")
                self.wakeword = MockWakeWordDetector(self.wakeword_settings.model_dump())

        # Audio Devices & VAD
        self.audio_input = AudioInputManager(sample_rate=self.settings.audio.sample_rate)
        self.audio_output = AudioOutputManager()
        self.vad = VoiceActivityDetector(
            energy_threshold=self.settings.audio.vad_energy_threshold,
            silence_duration_seconds=self.settings.audio.vad_silence_duration,
        )

    @property
    def privacy_status(self) -> str:
        """Exposes current microphone privacy state for UI rendering."""
        return self.state_machine.privacy_label

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status summary of active voice subsystem."""
        mic = AudioDeviceDiscovery.get_default_microphone()
        spk = AudioDeviceDiscovery.get_default_speaker()
        return {
            "enabled": self.settings.speech_to_text.enabled or self.settings.text_to_speech.enabled,
            "mode": self.settings.mode,
            "privacy_status": self.privacy_status,
            "microphone_state": self.state_machine.current_state.value,
            "audio_owner": self.ownership.current_owner,
            "wakeword_enabled": self.wakeword_settings.enabled,
            "wakeword_phrase": self.wakeword_settings.phrase,
            "wakeword_engine": type(self.wakeword).__name__,
            "wakeword_available": self.wakeword.is_available(),
            "stt_engine": type(self.stt).__name__,
            "stt_available": self.stt.is_available(),
            "tts_engine": type(self.tts).__name__,
            "tts_available": self.tts.is_available(),
            "microphone": mic.name if mic else "None detected",
            "speaker": spk.name if spk else "None detected",
            "push_to_talk": self.settings.push_to_talk,
        }

    def start_listening(self) -> bool:
        """Starts background wake-word listening."""
        if not self.wakeword_settings.enabled:
            logger.info("Wake-word listening is disabled in settings")
            return False

        if not self.ownership.acquire("wakeword"):
            logger.warning("Could not acquire microphone ownership lock for wake-word detector")
            return False

        if self.state_machine.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD, reason="Activated wake listening"):
            self.wakeword.start()
            return True
        return False

    def stop_listening(self) -> None:
        """Stops wake-word listening and releases microphone ownership."""
        self.wakeword.stop()
        self.ownership.release("wakeword")
        self.state_machine.transition_to(MicrophoneState.MICROPHONE_OFF, reason="Deactivated wake listening")

    def pause_listening(self) -> None:
        """Pauses wake-word listening."""
        self.wakeword.pause()
        self.state_machine.transition_to(MicrophoneState.PAUSED, reason="User paused listening")

    def resume_listening(self) -> None:
        """Resumes wake-word listening."""
        if self.state_machine.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD, reason="Resumed listening"):
            self.wakeword.resume()

    def fast_path_acknowledgement(self) -> None:
        """
        Fast-Path Acknowledgement: Plays predefined 'Yes, Boss?' response immediately
        without calling the expensive LLM.
        """
        if not self.wakeword_settings.acknowledgement:
            return

        ack_text = self.wakeword_settings.acknowledgement_text
        logger.info(f"Fast-path acknowledgement triggered: '{ack_text}'")
        self.tts.speak(ack_text)

    def handle_wake_detection(self, audio_chunk: Optional[bytes] = None) -> Optional[str]:
        """
        Workflow executed when wake word is detected:
        1. Transition state machine to WAKEWORD_DETECTED.
        2. Release wakeword audio lock.
        3. Check for single-utterance command ('JARVIS, open Chrome.').
        4. Fast-path acknowledgement ('Yes, Boss?').
        5. Acquire stt audio lock and capture command (handling timeout).
        6. Transcribe command and return text.
        """
        self.state_machine.transition_to(MicrophoneState.WAKEWORD_DETECTED, reason="Wake phrase detected")
        self.wakeword.pause()
        self.ownership.release("wakeword")

        # 1. Single-Utterance Check
        extracted_command = ""
        if audio_chunk and self.wakeword_settings.same_utterance_support:
            raw_transcript = self.stt.transcribe(audio_chunk)
            wake_found, command_part = self.wakeword.parse_single_utterance(raw_transcript)
            if wake_found and command_part:
                logger.info(f"Single-utterance command extracted: '{command_part}'")
                extracted_command = command_part

        # 2. Fast-Path Acknowledgement (if no same-utterance command extracted)
        if not extracted_command:
            self.fast_path_acknowledgement()

        # 3. If single-utterance command was captured, proceed directly to PROCESSING
        if extracted_command:
            self.state_machine.transition_to(MicrophoneState.PROCESSING, reason="Single-utterance command ready")
            return extracted_command

        # 4. Listen for command following acknowledgement
        if not self.ownership.acquire("stt"):
            logger.error("Failed to acquire microphone lock for STT command capture")
            self.start_listening()
            return None

        self.state_machine.transition_to(MicrophoneState.LISTENING_FOR_COMMAND, reason="Listening for Boss's command")

        # Capture command audio with timeout
        timeout = self.wakeword_settings.command_timeout_seconds
        command_audio = self.audio_input.record_seconds(duration_seconds=min(5.0, timeout))
        
        self.ownership.release("stt")

        if not command_audio or not self.vad.is_speech(command_audio):
            logger.info("Command listening timed out or received silence")
            self.state_machine.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD, reason="Command timeout")
            self.start_listening()
            return None

        self.state_machine.transition_to(MicrophoneState.PROCESSING, reason="Transcribing command")
        command_text = self.stt.transcribe(command_audio).strip()

        if not command_text:
            logger.info("Failed to transcribe speech command")
            self.start_listening()
            return None

        return command_text

    def listen_and_transcribe(self, duration_seconds: float = 3.0) -> str:
        """Push-to-Talk input fallback capturing audio directly."""
        if not self.ownership.acquire("push_to_talk"):
            logger.warning("Could not acquire microphone lock for push-to-talk")
            return ""

        self.state_machine.transition_to(MicrophoneState.LISTENING_FOR_COMMAND, reason="Push-to-talk active")
        try:
            pcm_bytes = self.audio_input.record_seconds(duration_seconds)
            self.ownership.release("push_to_talk")
            
            if not pcm_bytes or not self.vad.is_speech(pcm_bytes):
                self.start_listening()
                return ""

            self.state_machine.transition_to(MicrophoneState.PROCESSING, reason="Processing push-to-talk")
            text = self.stt.transcribe(pcm_bytes).strip()
            return text
        except Exception as e:
            self.ownership.release("push_to_talk")
            logger.error(f"Push-to-talk error: {e}")
            self.start_listening()
            return ""

    def speak(self, text: str) -> bool:
        """Synthesizes text via TTS while updating state machine to SPEAKING."""
        if not self.settings.text_to_speech.enabled or not text:
            return False

        self.state_machine.transition_to(MicrophoneState.SPEAKING, reason="Synthesizing response")
        try:
            res = self.tts.speak(text)
            self.start_listening()
            return res
        except Exception as e:
            logger.error(f"TTS output failed: {e}")
            self.start_listening()
            return False

    def speak_stream(self, token_generator: Generator[str, None, Any]) -> str:
        """Synthesizes text stream while in SPEAKING state."""
        self.state_machine.transition_to(MicrophoneState.SPEAKING, reason="Streaming response synthesis")
        try:
            if hasattr(self.tts, "speak_stream"):
                result = self.tts.speak_stream(token_generator)
            else:
                result = "".join(list(token_generator))
                self.tts.speak(result)
            self.start_listening()
            return result
        except Exception as e:
            logger.error(f"TTS stream output failed: {e}")
            self.start_listening()
            return "".join(list(token_generator))

    def interrupt(self) -> None:
        """
        Immediately interrupts active JARVIS speech playback and resets state machine
        back to LISTENING_FOR_WAKEWORD.
        """
        logger.info("TTS_STOPPED: Speech interrupted by Boss")
        self.tts.stop()
        self.audio_output.stop()
        self.start_listening()

    def stop_speech(self) -> None:
        """Alias for interrupt()."""
        self.interrupt()
