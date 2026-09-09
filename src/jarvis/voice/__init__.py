"""
JARVIS Voice Interface Subsystem.
"""

from jarvis.voice.audio_device import AudioDeviceDiscovery, AudioInputManager, AudioOutputManager
from jarvis.voice.vad import VoiceActivityDetector
from jarvis.voice.stt import SpeechRecognizer, LocalWhisperSTT, MockSpeechRecognizer
from jarvis.voice.tts import TextToSpeech, PyTTSx3TextToSpeech, MockTextToSpeech
from jarvis.voice.wakeword import WakeWordDetector, LocalWakeWordDetector, MockWakeWordDetector
from jarvis.voice.state_machine import VoiceStateMachine, MicrophoneState
from jarvis.voice.ownership import AudioOwnershipManager
from jarvis.voice.manager import VoiceManager

__all__ = [
    "AudioDeviceDiscovery",
    "AudioInputManager",
    "AudioOutputManager",
    "VoiceActivityDetector",
    "SpeechRecognizer",
    "LocalWhisperSTT",
    "MockSpeechRecognizer",
    "TextToSpeech",
    "PyTTSx3TextToSpeech",
    "MockTextToSpeech",
    "WakeWordDetector",
    "LocalWakeWordDetector",
    "MockWakeWordDetector",
    "VoiceStateMachine",
    "MicrophoneState",
    "AudioOwnershipManager",
    "VoiceManager",
]
