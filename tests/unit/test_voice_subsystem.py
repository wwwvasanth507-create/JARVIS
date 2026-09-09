"""
Unit tests for JARVIS Voice Subsystem (Audio Devices, VAD, STT, TTS, Manager).
Uses mock implementations to ensure non-blocking automated testing.
"""

import pytest
from jarvis.voice.audio_device import AudioDeviceDiscovery, AudioInputManager, AudioOutputManager
from jarvis.voice.vad import VoiceActivityDetector
from jarvis.voice.stt import MockSpeechRecognizer, LocalWhisperSTT
from jarvis.voice.tts import MockTextToSpeech, PyTTSx3TextToSpeech
from jarvis.voice.wakeword import MockWakeWordDetector
from jarvis.voice.manager import VoiceManager
from jarvis.core.config import VoiceSettings


def test_audio_device_discovery():
    mics = AudioDeviceDiscovery.list_microphones()
    speakers = AudioDeviceDiscovery.list_speakers()
    assert len(mics) > 0
    assert len(speakers) > 0
    
    default_mic = AudioDeviceDiscovery.get_default_microphone()
    assert default_mic is not None
    assert default_mic.name != ""


def test_voice_activity_detector():
    vad = VoiceActivityDetector(energy_threshold=100)
    
    # Silent buffer
    silent_pcm = b"\x00\x00" * 100
    assert vad.calculate_rms(silent_pcm) == 0.0
    assert not vad.is_speech(silent_pcm)

    # Active audio buffer
    loud_pcm = (b"\x00\x10\x00\x20" * 50)
    rms = vad.calculate_rms(loud_pcm)
    assert rms > 0.0


def test_mock_stt_and_tts():
    mock_stt = MockSpeechRecognizer(mock_transcript="Testing voice input")
    assert mock_stt.is_available()
    transcript = mock_stt.transcribe(b"dummy_pcm")
    assert transcript == "Testing voice input"

    mock_tts = MockTextToSpeech()
    assert mock_tts.is_available()
    voices = mock_tts.get_available_voices()
    assert len(voices) > 0
    assert mock_tts.speak("Testing voice output")


def test_pyttsx3_voice_discovery():
    tts = PyTTSx3TextToSpeech()
    if tts.is_available():
        voices = tts.get_available_voices()
        assert isinstance(voices, list)


def test_voice_manager_integration():
    settings = VoiceSettings(mode="hybrid")
    mock_stt = MockSpeechRecognizer(mock_transcript="Hello JARVIS")
    mock_tts = MockTextToSpeech()
    
    vm = VoiceManager(voice_settings=settings, stt=mock_stt, tts=mock_tts)
    status = vm.get_status()

    assert status["mode"] == "hybrid"
    assert status["stt_available"] is True
    assert status["tts_available"] is True

    # Test TTS execution
    assert vm.speak("Greetings Boss.") is True

    # Test streaming TTS synthesis
    def token_gen():
        yield "Of course, "
        yield "Boss. "
        yield "System operational."

    result_text = vm.speak_stream(token_gen())
    assert "Of course, Boss. System operational." in result_text


def test_wakeword_interface_readiness():
    ww = MockWakeWordDetector()
    ww.start()
    assert ww.is_active is True
    assert ww.is_detected(b"dummy_pcm") is False
    ww.stop()
    assert ww.is_active is False
