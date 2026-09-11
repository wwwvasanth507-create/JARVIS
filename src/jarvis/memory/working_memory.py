"""
Working Memory Manager for JARVIS.

Manages transient session state (current request, goal, plan, active entities, active app, active file,
recent observations, pending clarification/confirmation).
Expires with task/session and NEVER automatically turns into permanent memory.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkingMemorySession(BaseModel):
    session_id: str
    current_request: str = ""
    current_goal: str = ""
    current_plan: List[Dict[str, Any]] = Field(default_factory=list)
    active_entities: Dict[str, Any] = Field(default_factory=dict)
    active_application: Optional[str] = None
    active_file: Optional[str] = None
    active_browser_context: Dict[str, Any] = Field(default_factory=dict)
    recent_observations: List[Dict[str, Any]] = Field(default_factory=list)
    pending_clarification: Optional[Dict[str, Any]] = None
    pending_confirmation: Optional[Dict[str, Any]] = None
    created_at: float = Field(default_factory=time.time)
    last_active_at: float = Field(default_factory=time.time)


class WorkingMemoryManager:
    """Singleton managing transient Working Memory sessions."""

    _instance: Optional["WorkingMemoryManager"] = None

    def __init__(self):
        self._active_session: Optional[WorkingMemorySession] = None

    @classmethod
    def get_instance(cls) -> "WorkingMemoryManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_session(self, session_id: str, request_text: str = "") -> WorkingMemorySession:
        self._active_session = WorkingMemorySession(
            session_id=session_id,
            current_request=request_text,
            created_at=time.time(),
            last_active_at=time.time(),
        )
        logger.info(f"Started WorkingMemory session '{session_id}'")
        return self._active_session

    def get_session(self) -> Optional[WorkingMemorySession]:
        if self._active_session:
            self._active_session.last_active_at = time.time()
        return self._active_session

    def update_context(
        self,
        application: Optional[str] = None,
        file_path: Optional[str] = None,
        goal: Optional[str] = None,
        entity: Optional[Tuple[str, Any]] = None
    ) -> None:
        if not self._active_session:
            self.start_session("default_session")

        session = self._active_session
        if application:
            session.active_application = application
        if file_path:
            session.active_file = file_path
        if goal:
            session.current_goal = goal
        if entity:
            session.active_entities[entity[0]] = entity[1]

        session.last_active_at = time.time()

    def add_observation(self, source: str, data: Any) -> None:
        if not self._active_session:
            self.start_session("default_session")

        self._active_session.recent_observations.append({
            "source": source,
            "data": data,
            "timestamp": time.time(),
        })
        if len(self._active_session.recent_observations) > 20:
            self._active_session.recent_observations.pop(0)

    def clear_session(self) -> None:
        if self._active_session:
            logger.info(f"Expired WorkingMemory session '{self._active_session.session_id}'")
            self._active_session = None
