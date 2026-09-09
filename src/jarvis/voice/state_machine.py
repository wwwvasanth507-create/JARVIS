"""
Formal Microphone Privacy & Voice Listening State Machine for JARVIS.
Tracks listening states, enforces transition rules, logs audit events, and provides state callbacks.
"""

from enum import Enum
from typing import Callable, Dict, List, Optional, Set
import logging
import time

logger = logging.getLogger("jarvis.voice.state_machine")


class MicrophoneState(str, Enum):
    MICROPHONE_OFF = "MICROPHONE_OFF"
    LISTENING_FOR_WAKEWORD = "LISTENING_FOR_WAKEWORD"
    WAKEWORD_DETECTED = "WAKEWORD_DETECTED"
    LISTENING_FOR_COMMAND = "LISTENING_FOR_COMMAND"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class VoiceStateMachine:
    """
    State machine enforcing valid transitions for microphone listening and privacy status.
    """

    ALLOWED_TRANSITIONS: Dict[MicrophoneState, Set[MicrophoneState]] = {
        MicrophoneState.MICROPHONE_OFF: {
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.PAUSED,
            MicrophoneState.ERROR,
        },
        MicrophoneState.LISTENING_FOR_WAKEWORD: {
            MicrophoneState.WAKEWORD_DETECTED,
            MicrophoneState.LISTENING_FOR_COMMAND,
            MicrophoneState.PAUSED,
            MicrophoneState.MICROPHONE_OFF,
            MicrophoneState.ERROR,
        },
        MicrophoneState.WAKEWORD_DETECTED: {
            MicrophoneState.LISTENING_FOR_COMMAND,
            MicrophoneState.PROCESSING,
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.PAUSED,
            MicrophoneState.ERROR,
        },
        MicrophoneState.LISTENING_FOR_COMMAND: {
            MicrophoneState.PROCESSING,
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.PAUSED,
            MicrophoneState.ERROR,
        },
        MicrophoneState.PROCESSING: {
            MicrophoneState.SPEAKING,
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.PAUSED,
            MicrophoneState.ERROR,
        },
        MicrophoneState.SPEAKING: {
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.LISTENING_FOR_COMMAND,
            MicrophoneState.PAUSED,
            MicrophoneState.ERROR,
        },
        MicrophoneState.PAUSED: {
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.MICROPHONE_OFF,
            MicrophoneState.ERROR,
        },
        MicrophoneState.ERROR: {
            MicrophoneState.LISTENING_FOR_WAKEWORD,
            MicrophoneState.MICROPHONE_OFF,
            MicrophoneState.PAUSED,
        },
    }

    def __init__(self, initial_state: MicrophoneState = MicrophoneState.MICROPHONE_OFF):
        self._current_state = initial_state
        self._previous_state: Optional[MicrophoneState] = None
        self._last_state_change = time.time()
        self._callbacks: List[Callable[[MicrophoneState, MicrophoneState, Optional[str]], None]] = []

    @property
    def current_state(self) -> MicrophoneState:
        return self._current_state

    @property
    def previous_state(self) -> Optional[MicrophoneState]:
        return self._previous_state

    @property
    def privacy_label(self) -> str:
        """Returns human-readable privacy status label for UI exposure."""
        mapping = {
            MicrophoneState.MICROPHONE_OFF: "MIC OFF",
            MicrophoneState.LISTENING_FOR_WAKEWORD: "MIC LISTENING (Wake Word Only)",
            MicrophoneState.WAKEWORD_DETECTED: "MIC ACTIVE (Wake Detected)",
            MicrophoneState.LISTENING_FOR_COMMAND: "MIC ACTIVE (Listening for Command)",
            MicrophoneState.PROCESSING: "MIC BUSY (Processing Command)",
            MicrophoneState.SPEAKING: "MIC STANDBY (Speaking Response)",
            MicrophoneState.PAUSED: "MIC PAUSED",
            MicrophoneState.ERROR: "MIC ERROR",
        }
        return mapping.get(self._current_state, "MIC UNKNOWN")

    def register_callback(
        self, callback: Callable[[MicrophoneState, MicrophoneState, Optional[str]], None]
    ) -> None:
        self._callbacks.append(callback)

    def can_transition_to(self, new_state: MicrophoneState) -> bool:
        if new_state == self._current_state:
            return True
        allowed = self.ALLOWED_TRANSITIONS.get(self._current_state, set())
        return new_state in allowed

    def transition_to(self, new_state: MicrophoneState, reason: Optional[str] = None) -> bool:
        """Attempts to transition to a new state. Returns True if transition succeeded."""
        if new_state == self._current_state:
            return True

        if not self.can_transition_to(new_state):
            logger.warning(
                f"Invalid state transition attempted: {self._current_state.value} -> {new_state.value} (Reason: {reason})"
            )
            return False

        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state
        self._last_state_change = time.time()

        self._log_transition_event(old_state, new_state, reason)

        for cb in self._callbacks:
            try:
                cb(old_state, new_state, reason)
            except Exception as e:
                logger.error(f"Error in state transition callback: {e}")

        return True

    def _log_transition_event(
        self, old_state: MicrophoneState, new_state: MicrophoneState, reason: Optional[str]
    ) -> None:
        event_msg = f"STATE_CHANGE: {old_state.value} -> {new_state.value}"
        if reason:
            event_msg += f" ({reason})"

        if new_state == MicrophoneState.LISTENING_FOR_WAKEWORD:
            logger.info(f"WAKEWORD_STARTED: {event_msg}")
        elif new_state == MicrophoneState.WAKEWORD_DETECTED:
            logger.info(f"WAKEWORD_DETECTED: {event_msg}")
        elif new_state == MicrophoneState.LISTENING_FOR_COMMAND:
            logger.info(f"COMMAND_LISTENING_STARTED: {event_msg}")
        elif old_state == MicrophoneState.LISTENING_FOR_COMMAND:
            logger.info(f"COMMAND_LISTENING_STOPPED: {event_msg}")
        elif new_state == MicrophoneState.PROCESSING:
            logger.info(f"VOICE_PROCESSING_STARTED: {event_msg}")
        elif old_state == MicrophoneState.PROCESSING:
            logger.info(f"VOICE_PROCESSING_COMPLETED: {event_msg}")
        elif new_state == MicrophoneState.SPEAKING:
            logger.info(f"TTS_STARTED: {event_msg}")
        elif old_state == MicrophoneState.SPEAKING:
            logger.info(f"TTS_STOPPED: {event_msg}")
        elif new_state == MicrophoneState.PAUSED:
            logger.info(f"WAKEWORD_PAUSED: {event_msg}")
        else:
            logger.info(event_msg)
