"""
Application safety guard, protected software checker, and unsaved-work detector for JARVIS.
"""

from typing import List, Optional
from jarvis.applications.errors import ProtectedApplicationBlocked, UnsavedWorkWarning
from jarvis.applications.state import ApplicationInfo


DEFAULT_PROTECTED_NAMES = {
    "windows defender", "antivirus", "firewall", "task manager",
    "taskmgr.exe", "securityhealthservice.exe", "lsass.exe", "system"
}

EDITORS_WITH_UNSAVED_STATE = {
    "code.exe", "notepad.exe", "sublime_text.exe", "atom.exe", "notepad++.exe"
}


class ApplicationSafety:
    """Evaluates security rules and unsaved work warnings for applications."""

    def __init__(self, protected_names: Optional[List[str]] = None):
        self.protected_names = set(p.lower() for p in (protected_names or DEFAULT_PROTECTED_NAMES))

    def is_protected(self, app_info: ApplicationInfo) -> bool:
        """Returns True if application is a protected security/system component."""
        name_lower = app_info.name.lower()
        exe_lower = app_info.executable.lower()
        disp_lower = app_info.display_name.lower()

        return (
            name_lower in self.protected_names
            or exe_lower in self.protected_names
            or disp_lower in self.protected_names
        )

    def check_safety(self, app_info: ApplicationInfo, operation: str) -> None:
        """Validates safety for operation. Raises ProtectedApplicationBlocked if protected."""
        if self.is_protected(app_info) and operation in ("close", "restart", "terminate"):
            raise ProtectedApplicationBlocked(
                f"Operation '{operation}' on protected security application '{app_info.name}' is forbidden."
            )

    def detect_unsaved_work(self, app_info: ApplicationInfo) -> bool:
        """Checks if application is an editor known to hold unsaved work."""
        exe = app_info.executable.lower()
        return exe in EDITORS_WITH_UNSAVED_STATE
