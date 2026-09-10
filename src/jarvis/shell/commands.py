"""
Command categorization registry and fast-path resolution for JARVIS.
"""

from typing import Dict, Optional, Set
from jarvis.shell.parser import ParsedCommand


FAST_PATH_COMMANDS: Dict[str, Set[str]] = {
    "python": {"--version", "-v", "-V"},
    "python3": {"--version", "-v", "-V"},
    "py": {"--version", "-v", "-V"},
    "git": {"version", "--version", "status"},
    "node": {"--version", "-v"},
    "npm": {"--version", "-v"},
    "whoami": set(),
    "hostname": set(),
    "ver": set(),
    "uname": set(),
}


class CommandRegistry:
    """Fast-path lookup engine for deterministic status queries."""

    @staticmethod
    def is_fast_path(parsed: ParsedCommand) -> bool:
        """Returns True if the command is a simple deterministic read-only status query."""
        exe = parsed.executable.lower()
        if exe not in FAST_PATH_COMMANDS:
            return False
        sub_allowed = FAST_PATH_COMMANDS[exe]
        if not sub_allowed:
            return True
        if parsed.arguments and parsed.arguments[0].lower() in sub_allowed:
            return True
        return False
