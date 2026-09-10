"""
Application Launcher and Lifecycle Controller for JARVIS.
Handles application opening, closing, process launching, observation, and state verification.
"""

import subprocess
import time
import logging
from typing import Optional

from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.detector import ApplicationDetector
from jarvis.applications.models import ApplicationStatus
from jarvis.computer.base import ComputerActionResult
from jarvis.computer.windows.window import WindowsWindowManager

logger = logging.getLogger("jarvis.applications.launcher")


class ApplicationLauncher:
    """Launches and manages application processes with post-execution verification."""

    def __init__(self, registry: Optional[ApplicationRegistry] = None):
        self.registry = registry or ApplicationRegistry()

    def open_application(self, query: str) -> ComputerActionResult:
        """
        Resolves application alias, launches process, waits, observes, and verifies launch state.
        """
        start = time.perf_counter()
        entry = self.registry.resolve(query)
        if not entry:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Application query '{query}' could not be resolved in registry",
            )

        # Check if already running
        status_before = ApplicationDetector.get_status(entry)
        if status_before.is_running:
            # Focus existing window
            focus_res = WindowsWindowManager.focus_window(entry.executable)
            dur = time.perf_counter() - start
            return ComputerActionResult(
                success=True,
                status="SUCCESS",
                message=f"Application '{entry.name}' is already running. Focused active window.",
                data={"name": entry.name, "executable": entry.executable, "pids": status_before.process_ids},
                duration_seconds=round(dur, 4),
                verified=focus_res.verified,
            )

        # Launch process
        exec_path = status_before.resolved_path or entry.executable
        try:
            logger.info(f"Launching application '{entry.name}' via path: '{exec_path}'")
            proc = subprocess.Popen([exec_path], shell=False)

            # Wait briefly for startup
            time.sleep(1.0)

            # Observe and verify
            status_after = ApplicationDetector.get_status(entry)
            win_match = WindowsWindowManager._find_hwnd(entry.executable) or WindowsWindowManager._find_hwnd(entry.name)
            
            verified = status_after.is_running or (win_match is not None)
            dur = time.perf_counter() - start

            return ComputerActionResult(
                success=verified,
                status="SUCCESS" if verified else "UNCERTAIN",
                message=f"Launched '{entry.name}' (PID: {proc.pid})" if verified else f"Launched '{entry.name}', but verification uncertain.",
                data={
                    "name": entry.name,
                    "executable": entry.executable,
                    "pid": proc.pid,
                    "process_ids": status_after.process_ids,
                    "window_detected": bool(win_match),
                },
                duration_seconds=round(dur, 4),
                verified=verified,
            )
        except Exception as e:
            logger.error(f"Failed to launch application '{entry.name}': {e}")
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Failed to launch '{entry.name}': {str(e)}",
                duration_seconds=round(time.perf_counter() - start, 4),
            )

    def close_application(self, query: str, force: bool = False) -> ComputerActionResult:
        """
        Requests graceful closure of application window/process, observes, and verifies termination.
        """
        start = time.perf_counter()
        entry = self.registry.resolve(query)
        if not entry:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Application query '{query}' could not be resolved in registry",
            )

        status_before = ApplicationDetector.get_status(entry)
        if not status_before.is_running:
            # Check window too
            win_match = WindowsWindowManager._find_hwnd(entry.executable) or WindowsWindowManager._find_hwnd(entry.name)
            if not win_match:
                return ComputerActionResult(
                    success=True,
                    status="SUCCESS",
                    message=f"Application '{entry.name}' is not currently running.",
                    verified=True,
                )

        try:
            # 1. Try graceful window close first
            win_res = WindowsWindowManager.close_window(entry.executable)
            if not win_res.success:
                WindowsWindowManager.close_window(entry.name)

            time.sleep(0.5)

            # 2. Check if process is still running; force kill only if force parameter is True
            status_after = ApplicationDetector.get_status(entry)
            if status_after.is_running and force:
                logger.warning(f"Force closing application '{entry.name}' processes: {status_after.process_ids}")
                import psutil
                for pid in status_after.process_ids:
                    try:
                        p = psutil.Process(pid)
                        p.kill()
                    except Exception:
                        pass
                time.sleep(0.3)
                status_after = ApplicationDetector.get_status(entry)

            verified = not status_after.is_running
            dur = time.perf_counter() - start

            return ComputerActionResult(
                success=verified,
                status="SUCCESS" if verified else "UNCERTAIN",
                message=f"Closed application '{entry.name}'" if verified else f"Close request sent for '{entry.name}', process still active.",
                data={"name": entry.name, "is_running": status_after.is_running},
                duration_seconds=round(dur, 4),
                verified=verified,
            )
        except Exception as e:
            return ComputerActionResult(
                success=False,
                status="FAILED",
                message=f"Failed to close application '{entry.name}': {str(e)}",
                duration_seconds=round(time.perf_counter() - start, 4),
            )
