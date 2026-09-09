"""
Unit tests for AudioOwnershipManager microphone lock management.
"""

import pytest
import time
from jarvis.voice.ownership import AudioOwnershipManager


def test_audio_ownership_acquisition_and_release():
    mgr = AudioOwnershipManager(default_timeout_seconds=2.0)
    assert mgr.current_owner == "none"

    # Acquire lock for wakeword
    assert mgr.acquire("wakeword", timeout_seconds=0.5) is True
    assert mgr.current_owner == "wakeword"

    # Re-acquire by same owner succeeds
    assert mgr.acquire("wakeword", timeout_seconds=0.5) is True

    # Release lock
    mgr.release("wakeword")
    assert mgr.current_owner == "none"


def test_audio_ownership_conflict_rejection():
    mgr = AudioOwnershipManager(default_timeout_seconds=2.0)
    assert mgr.acquire("wakeword", timeout_seconds=0.5) is True

    # STT attempting to acquire while wakeword holds lock fails quickly
    assert mgr.acquire("stt", timeout_seconds=0.1) is False
    assert mgr.current_owner == "wakeword"

    mgr.release("wakeword")
    assert mgr.acquire("stt", timeout_seconds=0.5) is True
    assert mgr.current_owner == "stt"
    mgr.release("stt")


def test_audio_ownership_stale_lock_timeout():
    mgr = AudioOwnershipManager(default_timeout_seconds=0.1)
    assert mgr.acquire("stt") is True
    assert mgr.current_owner == "stt"

    time.sleep(0.15)
    # Stale lock resets automatically
    assert mgr.current_owner == "none"
