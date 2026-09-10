"""
Observation Manager for JARVIS orchestration.
"""

from typing import Any, Dict, List
from jarvis.tools.base import ToolResult


class ObservationManager:
    """Collects and structures observations from executed tool actions."""

    def __init__(self):
        self.observations: List[Dict[str, Any]] = []

    def observe(self, tool_name: str, arguments: Dict[str, Any], result: ToolResult) -> Dict[str, Any]:
        obs = {
            "tool_name": tool_name,
            "success": result.success,
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "data": result.data,
            "error": result.error,
            "verification": result.verification,
            "duration_ms": result.duration_ms,
        }

        # Subsystem-specific extraction
        if "application" in tool_name:
            obs["subsystem"] = "application"
            obs["application_target"] = arguments.get("application") or arguments.get("name")
        elif "filesystem" in tool_name:
            obs["subsystem"] = "filesystem"
            obs["file_target"] = arguments.get("path") or arguments.get("query")
        elif "browser" in tool_name:
            obs["subsystem"] = "browser"
            obs["url_target"] = arguments.get("url") or arguments.get("query")
        elif "shell" in tool_name:
            obs["subsystem"] = "shell"
            obs["command_target"] = arguments.get("command")
        else:
            obs["subsystem"] = "generic"

        self.observations.append(obs)
        return obs

    def detect_semantic_loop(self, tool_name: str, arguments: Dict[str, Any], max_allowed: int = 3) -> bool:
        """Detects repeated identical or semantically identical tool invocations."""
        count = 0
        for obs in self.observations:
            if obs.get("tool_name") == tool_name:
                count += 1
        return count >= max_allowed

    def get_summary(self) -> List[Dict[str, Any]]:
        return self.observations
