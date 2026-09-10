"""
Application Lifecycle Management for JARVIS.

Defines explicit application states, state transitions, and an idempotent lifecycle manager.
"""

from enum import Enum, auto
import logging
from threading import RLock
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


class ApplicationState(Enum):
    """Explicit application lifecycle states."""
    CREATED = auto()
    VALIDATING = auto()
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()


class ApplicationLifecycleError(Exception):
    """Base exception for application lifecycle errors."""
    pass


class InvalidStateTransitionError(ApplicationLifecycleError):
    """Raised when an invalid state transition is requested."""
    pass


class LifecycleManager:
    """
    Manages application state transitions safely and idempotently.
    Allows registering state change listeners.
    """

    ALLOWED_TRANSITIONS = {
        ApplicationState.CREATED: {ApplicationState.VALIDATING, ApplicationState.INITIALIZING, ApplicationState.STOPPING, ApplicationState.FAILED},
        ApplicationState.VALIDATING: {ApplicationState.INITIALIZING, ApplicationState.FAILED, ApplicationState.STOPPING},
        ApplicationState.INITIALIZING: {ApplicationState.READY, ApplicationState.FAILED, ApplicationState.STOPPING},
        ApplicationState.READY: {ApplicationState.RUNNING, ApplicationState.PAUSING, ApplicationState.STOPPING, ApplicationState.FAILED},
        ApplicationState.RUNNING: {ApplicationState.PAUSING, ApplicationState.STOPPING, ApplicationState.FAILED, ApplicationState.READY},
        ApplicationState.PAUSING: {ApplicationState.READY, ApplicationState.STOPPING, ApplicationState.FAILED},
        ApplicationState.STOPPING: {ApplicationState.STOPPED, ApplicationState.FAILED},
        ApplicationState.STOPPED: {ApplicationState.INITIALIZING},
        ApplicationState.FAILED: {ApplicationState.STOPPING, ApplicationState.STOPPED, ApplicationState.INITIALIZING},
    }

    def __init__(self, initial_state: ApplicationState = ApplicationState.CREATED):
        self._state = initial_state
        self._lock = RLock()
        self._listeners: List[Callable[[ApplicationState, ApplicationState], None]] = []

    @property
    def state(self) -> ApplicationState:
        with self._lock:
            return self._state

    def is_running(self) -> bool:
        with self._lock:
            return self._state == ApplicationState.RUNNING

    def is_ready(self) -> bool:
        with self._lock:
            return self._state in (ApplicationState.READY, ApplicationState.RUNNING)

    def is_stopped(self) -> bool:
        with self._lock:
            return self._state in (ApplicationState.STOPPED, ApplicationState.FAILED)

    def add_listener(self, listener: Callable[[ApplicationState, ApplicationState], None]) -> None:
        """Register a callback (old_state, new_state) -> None."""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ApplicationState, ApplicationState], None]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def transition_to(self, new_state: ApplicationState) -> bool:
        """
        Transition application to a new state if allowed.
        Idempotent: if already in target state, returns True without error.
        """
        with self._lock:
            if self._state == new_state:
                logger.debug(f"Lifecycle already in state: {new_state.name}")
                return True

            allowed = self.ALLOWED_TRANSITIONS.get(self._state, set())
            if new_state not in allowed:
                msg = f"Cannot transition from {self._state.name} to {new_state.name}"
                logger.error(msg)
                raise InvalidStateTransitionError(msg)

            old_state = self._state
            self._state = new_state
            logger.info(f"Application state transition: {old_state.name} -> {new_state.name}")

            for listener in list(self._listeners):
                try:
                    listener(old_state, new_state)
                except Exception as e:
                    logger.error(f"Error in lifecycle listener on state change {old_state.name} -> {new_state.name}: {e}")

            return True
