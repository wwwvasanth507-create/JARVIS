"""
Intent Understanding and Parsing module for JARVIS.
"""

import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from jarvis.security.permissions import RiskLevel


class IntentConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClarificationRequest(BaseModel):
    question: str
    missing_information: str
    candidates: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class Intent(BaseModel):
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    entities: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    confidence: IntentConfidence = IntentConfidence.HIGH
    risk_level: RiskLevel = RiskLevel.LOW
    requires_clarification: bool = False
    clarification: Optional[ClarificationRequest] = None
    is_fast_path: bool = False
    direct_tool_name: Optional[str] = None


class IntentParser:
    """Parses natural language requests into structured Intents."""

    FAST_PATH_PATTERNS = [
        # Applications
        (r"^(?:open|launch|start)\s+([a-zA-Z0-9_\-\.\s]+)$", "application.open", "application"),
        (r"^(?:close|quit|terminate)\s+([a-zA-Z0-9_\-\.\s]+)$", "application.close", "application"),
        (r"^is\s+([a-zA-Z0-9_\-\.\s]+)\s+running\??$", "application.is_running", "application"),
        (r"^(?:focus|switch to)\s+([a-zA-Z0-9_\-\.\s]+)$", "application.focus", "application"),
        (r"^list running applications\??$", "application.list_running", None),
        (r"^list installed applications\??$", "application.list", None),
        
        # Filesystem
        (r"^(?:list|show)\s+(?:files in|directory|folder)?\s*(.*)$", "filesystem.list_directory", "path"),
        (r"^search\s+(?:for\s+)?([a-zA-Z0-9_\-\.\*]+)(?:\s+in\s+(.*))?$", "filesystem.search", "query"),
        (r"^read\s+file\s+(.*)$", "filesystem.read_file", "path"),
        
        # Computer
        (r"^list windows\??$", "computer.list_windows", None),
        (r"^show active window\??$", "computer.get_active_window", None),
        
        # Shell
        (r"^run command\s+(.*)$", "shell.execute", "command"),
        (r"^check git status$", "shell.execute", None),
        
        # Browser
        (r"^open url\s+(https?://\S+)$", "browser.open", "url"),
    ]

    def __init__(self, brain: Optional[Any] = None):
        self.brain = brain

    def parse(self, request: str) -> Intent:
        normalized = request.strip().rstrip(".!?").strip()

        # Check direct fast path
        fast_intent = self._try_fast_path(normalized)
        if fast_intent:
            return fast_intent

        # General LLM or rule fallback
        return self._fallback_parse(normalized)

    def _try_fast_path(self, text: str) -> Optional[Intent]:
        for pattern, tool_name, primary_param in self.FAST_PATH_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                params = {}
                target_val = None
                if primary_param and match.groups():
                    val = match.group(1).strip()
                    params[primary_param] = val
                    target_val = val
                if tool_name == "filesystem.search":
                    params = {
                        "pattern": match.group(1).strip(),
                        "root_path": match.group(2).strip() if (len(match.groups()) > 1 and match.group(2)) else ".",
                    }
                    target_val = params["pattern"]

                if text.lower() == "check git status":
                    tool_name = "shell.execute"
                    params = {"command": "git status"}
                    target_val = "git status"

                risk = RiskLevel.LOW
                if tool_name in ("shell.execute", "application.close"):
                    risk = RiskLevel.MEDIUM

                return Intent(
                    action=tool_name,
                    target=target_val,
                    parameters=params,
                    confidence=IntentConfidence.HIGH,
                    risk_level=risk,
                    is_fast_path=True,
                    direct_tool_name=tool_name,
                )
        return None

    def _fallback_parse(self, text: str) -> Intent:
        # Check basic keyword heuristics if brain is unavailable
        lower = text.lower()
        if "open" in lower and "code" in lower:
            return Intent(
                action="application.open",
                target="VS Code",
                parameters={"application": "VS Code"},
                confidence=IntentConfidence.HIGH,
                risk_level=RiskLevel.LOW,
                is_fast_path=True,
                direct_tool_name="application.open",
            )
        if "find" in lower or "search" in lower:
            return Intent(
                action="filesystem.search",
                target=text,
                parameters={"query": text},
                confidence=IntentConfidence.MEDIUM,
                risk_level=RiskLevel.LOW,
            )

        # Default structured intent
        return Intent(
            action="general.task",
            target=text,
            parameters={"query": text},
            confidence=IntentConfidence.MEDIUM,
            risk_level=RiskLevel.LOW,
        )
