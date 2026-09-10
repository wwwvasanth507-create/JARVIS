"""
Lightweight Local Event Bus & Event Deduplicator for JARVIS.

Provides typed event dispatch, listener registration, event coalescing, and memory isolation.
"""

from enum import Enum
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SystemEventType(str, Enum):
    APPLICATION_STARTED = "APPLICATION_STARTED"
    APPLICATION_STOPPED = "APPLICATION_STOPPED"
    WINDOW_FOCUSED = "WINDOW_FOCUSED"
    FILE_CREATED = "FILE_CREATED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_DELETED = "FILE_DELETED"
    BROWSER_NAVIGATED = "BROWSER_NAVIGATED"
    DOWNLOAD_STARTED = "DOWNLOAD_STARTED"
    DOWNLOAD_COMPLETED = "DOWNLOAD_COMPLETED"
    TASK_STARTED = "TASK_STARTED"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_FAILED = "TASK_FAILED"
    TASK_COMPLETED = "TASK_COMPLETED"
    VOICE_STARTED = "VOICE_STARTED"
    VOICE_STOPPED = "VOICE_STOPPED"


class SystemEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SystemEventType
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class JarvisEventBus:
    """Singleton local event bus providing event publishing, listener registration, and coalescing."""

    _instance: Optional["JarvisEventBus"] = None

    def __init__(self):
        self._listeners: Dict[SystemEventType, List[Callable[[SystemEvent], None]]] = {}
        self._recent_events: List[SystemEvent] = []
        self._last_event_time: Dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> "JarvisEventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: SystemEventType, listener: Callable[[SystemEvent], None]) -> None:
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def publish(self, event_type: SystemEventType, source: str, data: Optional[Dict[str, Any]] = None) -> SystemEvent:
        now = time.time()
        coalesce_key = f"{event_type.value}_{source}"
        if coalesce_key in self._last_event_time and (now - self._last_event_time[coalesce_key]) < 0.5:
            # Deduplicate rapid duplicate events
            logger.debug(f"EventBus coalesced duplicate event '{coalesce_key}'")
            return self._recent_events[-1] if self._recent_events else SystemEvent(event_type=event_type, source=source)

        self._last_event_time[coalesce_key] = now
        event = SystemEvent(event_type=event_type, source=source, data=data or {}, timestamp=now)
        self._recent_events.append(event)
        if len(self._recent_events) > 100:
            self._recent_events.pop(0)

        listeners = self._listeners.get(event_type, [])
        for cb in listeners:
            try:
                cb(event)
            except Exception as e:
                logger.warning(f"Error in EventBus listener for '{event_type.value}': {e}")

        return event

    def get_recent_events(self, event_type: Optional[SystemEventType] = None) -> List[SystemEvent]:
        if event_type is None:
            return list(reversed(self._recent_events))
        return [e for e in reversed(self._recent_events) if e.event_type == event_type]
