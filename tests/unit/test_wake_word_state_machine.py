"""
Unit tests for VoiceStateMachine transition logic and microphone privacy state tracking.
"""

import pytest
from jarvis.voice.state_machine import VoiceStateMachine, MicrophoneState


def test_initial_state():
    sm = VoiceStateMachine()
    assert sm.current_state == MicrophoneState.MICROPHONE_OFF
    assert sm.previous_state is None
    assert sm.privacy_label == "MIC OFF"


def test_valid_state_transitions():
    sm = VoiceStateMachine(initial_state=MicrophoneState.MICROPHONE_OFF)

    # Off -> Listening for Wakeword
    assert sm.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD) is True
    assert sm.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD
    assert sm.privacy_label == "MIC LISTENING (Wake Word Only)"

    # Listening -> Wakeword Detected
    assert sm.transition_to(MicrophoneState.WAKEWORD_DETECTED) is True
    assert sm.current_state == MicrophoneState.WAKEWORD_DETECTED
    assert sm.privacy_label == "MIC ACTIVE (Wake Detected)"

    # Wakeword Detected -> Listening for Command
    assert sm.transition_to(MicrophoneState.LISTENING_FOR_COMMAND) is True
    assert sm.current_state == MicrophoneState.LISTENING_FOR_COMMAND

    # Listening for Command -> Processing
    assert sm.transition_to(MicrophoneState.PROCESSING) is True
    assert sm.current_state == MicrophoneState.PROCESSING

    # Processing -> Speaking
    assert sm.transition_to(MicrophoneState.SPEAKING) is True
    assert sm.current_state == MicrophoneState.SPEAKING

    # Speaking -> Listening for Wakeword
    assert sm.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD) is True
    assert sm.current_state == MicrophoneState.LISTENING_FOR_WAKEWORD


def test_invalid_state_transition_rejection():
    sm = VoiceStateMachine(initial_state=MicrophoneState.MICROPHONE_OFF)

    # Invalid: Off directly to Speaking
    assert sm.can_transition_to(MicrophoneState.SPEAKING) is False
    assert sm.transition_to(MicrophoneState.SPEAKING) is False
    assert sm.current_state == MicrophoneState.MICROPHONE_OFF


def test_state_change_callbacks():
    sm = VoiceStateMachine(initial_state=MicrophoneState.MICROPHONE_OFF)
    events = []

    def on_change(old_state, new_state, reason):
        events.append((old_state, new_state, reason))

    sm.register_callback(on_change)
    sm.transition_to(MicrophoneState.LISTENING_FOR_WAKEWORD, reason="Startup")

    assert len(events) == 1
    assert events[0] == (MicrophoneState.MICROPHONE_OFF, MicrophoneState.LISTENING_FOR_WAKEWORD, "Startup")
