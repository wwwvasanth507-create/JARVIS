"""
Application lifecycle controller (graceful close, focus, restart, health, readiness) for JARVIS.
"""

import time
import psutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from jarvis.applications.errors import ApplicationCloseFailed, ApplicationNotRunning
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.process import ApplicationProcess
from jarvis.applications.safety import ApplicationSafety
from jarvis.applications.state import ApplicationHealth, ApplicationInfo, CloseResult, LaunchResult
from jarvis.applications.verification import ApplicationVerifier
from jarvis.computer.windows.window import WindowsWindowManager as WindowManager


class ApplicationController:
    """Controls running applications (graceful termination, window focus, health, readiness)."""

    def __init__(
        self,
        launcher: Optional[ApplicationLauncher] = None,
        safety: Optional[ApplicationSafety] = None,
    ):
        self.launcher = launcher or ApplicationLauncher()
        self.safety = safety or ApplicationSafety()

    def close_application(self, app_info: ApplicationInfo, force: bool = False) -> CloseResult:
        """
        Closes an application gracefully.
        Checks protected status and unsaved work before taking action.
        """
        self.safety.check_safety(app_info, "close")

        pids = ApplicationProcess.find_pids_for_executable(app_info.executable)
        if not pids:
            return CloseResult(
                success=True,
                application=app_info.name,
                status="stopped",
                graceful=True,
                has_unsaved_work=False,
                verified=True,
                message=f"Application '{app_info.name}' was not running.",
            )

        has_unsaved = self.safety.detect_unsaved_work(app_info)
        if has_unsaved and not force:
            return CloseResult(
                success=False,
                application=app_info.name,
                status="unsaved_work_detected",
                graceful=False,
                has_unsaved_work=True,
                verified=False,
                message=(
                    f"Application '{app_info.name}' may have unsaved changes. "
                    "Force close was not requested, so the application was left open."
                ),
            )

        for pid in pids:
            try:
                p = psutil.Process(pid)
                if force:
                    p.kill()
                else:
                    p.terminate()
            except Exception:
                continue

        verified_stopped = ApplicationVerifier.verify_stopped(app_info, timeout=4.0)

        if not verified_stopped and not force:
            return CloseResult(
                success=False,
                application=app_info.name,
                status="close_failed",
                graceful=True,
                has_unsaved_work=False,
                verified=False,
                message=f"Application '{app_info.name}' did not stop gracefully.",
            )

        return CloseResult(
            success=verified_stopped,
            application=app_info.name,
            status="stopped" if verified_stopped else "failed_to_stop",
            graceful=not force,
            has_unsaved_work=False,
            verified=verified_stopped,
            message=f"Application '{app_info.name}' closed successfully.",
        )

    def restart_application(self, app_info: ApplicationInfo) -> LaunchResult:
        """Restarts application safely."""
        self.close_application(app_info, force=False)
        return self.launcher.open_application(app_info)

    def focus_application(self, app_info: ApplicationInfo) -> bool:
        """Focuses target application window using Prompt 005's WindowManager."""
        pids = ApplicationProcess.find_pids_for_executable(app_info.executable)
        if not pids:
            raise ApplicationNotRunning(f"Application '{app_info.name}' is not running.")

        try:
            wm = WindowManager()
            windows = wm.list_windows()
            for w in windows:
                if w.process_id in pids or app_info.name.lower() in w.title.lower():
                    return wm.focus_window(w.handle)
            # Fallback focus first window
            if windows:
                return wm.focus_window(windows[0].handle)
            return False
        except Exception:
            return False

    def wait_until_ready(self, app_info: ApplicationInfo, timeout: float = 15.0) -> bool:
        """Polls until application starts and becomes responsive."""
        ok, pids = ApplicationVerifier.verify_started(app_info, timeout=timeout)
        return ok

    def check_health(self, app_info: ApplicationInfo) -> ApplicationHealth:
        """Returns detailed health status for app_info."""
        pids = ApplicationProcess.find_pids_for_executable(app_info.executable)
        is_running = len(pids) > 0
        responsive = True

        if is_running:
            try:
                p = psutil.Process(pids[0])
                status_str = p.status()
                if status_str in ("zombie", "dead"):
                    responsive = False
            except Exception:
                responsive = False

        now_str = datetime.now(timezone.utc).isoformat()

        return ApplicationHealth(
            name=app_info.name,
            running=is_running,
            responsive=responsive,
            window_count=len(pids),
            pids=pids,
            status="healthy" if (is_running and responsive) else ("stopped" if not is_running else "unresponsive"),
            last_checked=now_str,
        )
