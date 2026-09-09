"""
Unit tests for WakeWordDetector abstractions, single-utterance parsing, and cooldown enforcement.
"""

import pytest
import time
from jarvis.voice.wakeword import MockWakeWordDetector, LocalWakeWordDetector


def test_mock_wakeword_detector_lifecycle():
    ww = MockWakeWordDetector(config={"phrase": "JARVIS", "cooldown_seconds": 0.5})
    assert ww.is_available() is True
    assert ww.is_active is False

    ww.start()
    assert ww.is_active is True
    assert ww.is_paused is False

    # Detection when not triggered
    assert ww.is_detected(b"dummy") is False

    # Trigger wake event
    ww.trigger_wake_event()
    assert ww.is_detected(b"dummy") is True

    # Cooldown enforcement prevents immediate re-trigger
    ww.trigger_wake_event()
    assert ww.is_detected(b"dummy") is False

    time.sleep(0.55)
    assert ww.is_detected(b"dummy") is True

    ww.pause()
    assert ww.is_paused is True
    ww.trigger_wake_event()
    assert ww.is_detected(b"dummy") is False

    ww.resume()
    assert ww.is_paused is False

    ww.stop()
    assert ww.is_active is False


def test_single_utterance_parsing():
    ww = MockWakeWordDetector(config={"phrase": "JARVIS", "secondary_phrases": ["HEY JARVIS"]})

    # Test 1: Just wake word
    wake_found, command = ww.parse_single_utterance("JARVIS")
    assert wake_found is True
    assert command == ""

    # Test 2: Same-utterance phrase and command
    wake_found, command = ww.parse_single_utterance("JARVIS, open Chrome and play music")
    assert wake_found is True
    assert command == "OPEN CHROME AND PLAY MUSIC"

    # Test 3: Secondary phrase
    wake_found, command = ww.parse_single_utterance("Hey JARVIS, report status")
    assert wake_found is True
    assert command == "REPORT STATUS"

    # Test 4: Unrelated phrase
    wake_found, command = ww.parse_single_utterance("What is the current time?")
    assert wake_found is False
    assert command == ""


def test_local_wakeword_fallback_behavior():
    local_ww = LocalWakeWordDetector(config={"model_path": "models/wakeword/nonexistent.onnx"})
    # Should fall back cleanly without crashing
    assert isinstance(local_ww.is_available(), bool)
