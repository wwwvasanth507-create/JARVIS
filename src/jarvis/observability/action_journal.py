"""
User-Facing Action Journal for JARVIS Observability.

Records recent meaningful assistant actions, workflow executions, task replays,
and automation runs with credential/secret redaction.
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ActionJournalEntry(BaseModel):
    entry_id: str
    action_type: str  # "TOOL_EXECUTION", "WORKFLOW", "AUTOMATION", "MONITOR"
    summary: str
    status: str = "SUCCESS"
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class ActionJournal:
    """Singleton user-facing journal logging assistant operations."""

    _instance: Optional["ActionJournal"] = None
    SECRET_PATTERN = r"(?:key|password|secret|token|auth)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?"

    def __init__(self):
        self._entries: List[ActionJournalEntry] = []
        self._max_entries: int = 200

    @classmethod
    def get_instance(cls) -> "ActionJournal":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log_action(self, action_type: str, summary: str, status: str = "SUCCESS", details: Optional[Dict[str, Any]] = None) -> ActionJournalEntry:
        clean_summary = self._redact_secrets(summary)
        clean_details = self._sanitize_dict(details or {})

        entry = ActionJournalEntry(
            entry_id=f"act_{len(self._entries)+1}",
            action_type=action_type,
            summary=clean_summary,
            status=status,
            details=clean_details,
            timestamp=time.time()
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

        logger.info(f"ActionJournal [{action_type}] {clean_summary} ({status})")
        return entry

    def get_entries(self, limit: int = 50, action_type: Optional[str] = None) -> List[ActionJournalEntry]:
        res = self._entries
        if action_type:
            res = [e for e in res if e.action_type == action_type]
        return list(reversed(res[-limit:]))

    def _redact_secrets(self, text: str) -> str:
        return re.sub(r"((?:key|password|secret|token|auth)\s*[:=]\s*)['\"]?([^\s'\"]+)['\"]?", r"\1[REDACTED]", text, flags=re.IGNORECASE)

    def _sanitize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        res = {}
        for k, v in d.items():
            if any(s in k.lower() for s in ("password", "secret", "token", "key", "credential")):
                res[k] = "[REDACTED]"
            elif isinstance(v, dict):
                res[k] = self._sanitize_dict(v)
            else:
                res[k] = v
        return res
