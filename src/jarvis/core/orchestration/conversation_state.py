"""
Structured Conversation and Task State Manager for JARVIS Orchestration.

Tracks active entity, application, browser page, file, document, recent tool outputs,
and pending clarification/confirmation states across user interactions.
"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActiveEntity(BaseModel):
    name: str
    entity_type: str  # "file", "application", "url", "document", "task"
    value: str
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Bounded, privacy-filtered active conversation and task state."""

    active_request: Optional[str] = None
    active_goal: Optional[str] = None
    active_application: Optional[str] = None
    active_browser_page: Optional[Dict[str, Any]] = None  # {url, title, results}
    active_file: Optional[str] = None
    active_document: Optional[Dict[str, Any]] = None
    active_entities: List[ActiveEntity] = Field(default_factory=list)
    recent_tool_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    max_recent_outputs: int = 10
    pending_confirmation: Optional[Dict[str, Any]] = None
    pending_clarification: Optional[Dict[str, Any]] = None
    pending_human_intervention: Optional[Dict[str, Any]] = None
    last_updated: float = Field(default_factory=time.time)

    def record_entity(self, name: str, entity_type: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Records or updates an active entity in conversation context."""
        # Remove existing entity with same name/value if present
        self.active_entities = [e for e in self.active_entities if not (e.name == name and e.value == value)]
        self.active_entities.append(ActiveEntity(
            name=name,
            entity_type=entity_type,
            value=value,
            metadata=metadata or {}
        ))
        # Keep bounded to last 15 entities
        if len(self.active_entities) > 15:
            self.active_entities.pop(0)
        self.last_updated = time.time()

    def record_tool_output(self, tool_name: str, action: str, output: Any, status: str = "SUCCESS") -> None:
        """Records recent tool execution output for context reference resolution."""
        self.recent_tool_outputs.append({
            "tool_name": tool_name,
            "action": action,
            "output": output,
            "status": status,
            "timestamp": time.time()
        })
        if len(self.recent_tool_outputs) > self.max_recent_outputs:
            self.recent_tool_outputs.pop(0)

        # Automatically update active application, file, or browser page
        if tool_name.startswith("application."):
            if isinstance(output, dict) and "application" in output:
                self.active_application = output["application"]
        elif tool_name.startswith("filesystem.") or tool_name.startswith("document.") or tool_name.startswith("file."):
            if isinstance(output, str) and (output.endswith(".txt") or output.endswith(".md") or output.endswith(".pdf")):
                self.active_file = output
                self.record_entity("active_file", "file", output)
            elif isinstance(output, dict) and "path" in output:
                self.active_file = str(output["path"])
                self.record_entity("active_file", "file", str(output["path"]))
            elif isinstance(output, dict) and "matches" in output and isinstance(output["matches"], list) and len(output["matches"]) > 0:
                self.active_file = str(output["matches"][0])
                self.record_entity("active_file", "file", str(output["matches"][0]))
        elif tool_name.startswith("browser."):
            if isinstance(output, dict) and ("url" in output or "title" in output or "results" in output):
                self.active_browser_page = output

        self.last_updated = time.time()

    def get_latest_entity(self, entity_type: Optional[str] = None) -> Optional[ActiveEntity]:
        """Returns the most recently recorded entity matching specified type."""
        for entity in reversed(self.active_entities):
            if entity_type is None or entity.entity_type == entity_type:
                return entity
        return None

    def clear(self) -> None:
        """Resets active conversation state."""
        self.active_request = None
        self.active_goal = None
        self.active_application = None
        self.active_browser_page = None
        self.active_file = None
        self.active_document = None
        self.active_entities.clear()
        self.recent_tool_outputs.clear()
        self.pending_confirmation = None
        self.pending_clarification = None
        self.pending_human_intervention = None
        self.last_updated = time.time()


class ConversationStateManager:
    """Singleton/Manager providing safe access to active ConversationState."""

    _instance: Optional["ConversationStateManager"] = None

    def __init__(self):
        self.state = ConversationState()

    @classmethod
    def get_instance(cls) -> "ConversationStateManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_tool_output(self, tool_name: str, action: str, output: Any, status: str = "SUCCESS") -> None:
        self.state.record_tool_output(tool_name=tool_name, action=action, output=output, status=status)

    def set_active_task(self, task_id: str, description: str) -> None:
        self.state.active_goal = task_id
        self.state.active_request = description

    def reset(self) -> None:
        self.state.clear()
