"""
Application Discovery and Process Detector for JARVIS.
Checks active processes via psutil and locates application executable paths.
"""

import os
from pathlib import Path
from typing import List, Optional
import psutil
import logging

from jarvis.applications.models import ApplicationEntry, ApplicationStatus

logger = logging.getLogger("jarvis.applications.detector")


class ApplicationDetector:
    """Discovers installed applications and observes active system processes."""

    @staticmethod
    def is_running(executable_name: str) -> bool:
        exec_lower = executable_name.lower()
        try:
            for proc in psutil.process_iter(["name"]):
                if (proc.info.get("name") or "").lower() == exec_lower:
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def get_status(cls, entry: ApplicationEntry) -> ApplicationStatus:
        exec_name = entry.executable.lower()
        target_names = [exec_name] + [a.lower() for a in entry.aliases if a.lower().endswith(".exe")]
        pids: List[int] = []
        resolved_path: Optional[str] = None
        try:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    pname = (proc.info.get("name") or "").lower()
                    if any(tn in pname for tn in target_names):
                        pids.append(proc.info["pid"])
                        if not resolved_path and proc.info.get("exe"):
                            resolved_path = proc.info["exe"]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Error inspecting processes: {e}")

        if not resolved_path:
            resolved_path = cls.resolve_executable_path(entry)

        return ApplicationStatus(
            name=entry.name,
            executable=entry.executable,
            is_running=len(pids) > 0,
            process_ids=pids,
            resolved_path=resolved_path,
        )

    @classmethod
    def resolve_executable_path(cls, entry: ApplicationEntry) -> Optional[str]:
        """Locates actual filesystem executable path for an application entry."""
        # 1. Check configured common_paths
        for cp in entry.common_paths:
            expanded = os.path.expandvars(cp)
            p = Path(expanded)
            if p.exists() and p.is_file():
                return str(p)

        # 2. Check PATH environment
        exec_name = entry.executable
        path_env = os.environ.get("PATH", "").split(os.pathsep)
        for d in path_env:
            candidate = Path(d) / exec_name
            if candidate.exists() and candidate.is_file():
                return str(candidate)

        # Return executable string directly for standard system commands (e.g. calc.exe, notepad.exe)
        return exec_name
