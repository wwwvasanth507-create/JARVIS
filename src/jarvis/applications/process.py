"""
Application process inspection and running state detector for JARVIS.
"""

import psutil
from typing import List, Optional
from jarvis.applications.state import ApplicationInfo, ApplicationState


class ApplicationProcess:
    """Queries running OS processes to check application state and metrics."""

    @staticmethod
    def find_pids_for_executable(executable_name: str) -> List[int]:
        """Returns PIDs of processes matching executable_name."""
        target_name = executable_name.lower()
        matched_pids: List[int] = []

        for p in psutil.process_iter(['pid', 'name']):
            try:
                name = p.info['name']
                if name and name.lower() == target_name:
                    matched_pids.append(p.info['pid'])
            except Exception:
                continue

        return matched_pids

    @classmethod
    def get_application_state(cls, app_info: ApplicationInfo) -> ApplicationState:
        """Retrieves running ApplicationState for app_info."""
        pids = cls.find_pids_for_executable(app_info.executable)
        is_running = len(pids) > 0

        total_cpu = 0.0
        total_mem = 0.0
        launch_time_str = None

        if is_running:
            for pid in pids:
                try:
                    p = psutil.Process(pid)
                    total_cpu += p.cpu_percent(interval=None) or 0.0
                    total_mem += p.memory_percent() or 0.0
                    if not launch_time_str:
                        launch_time_str = str(p.create_time())
                except Exception:
                    continue

        return ApplicationState(
            name=app_info.name,
            display_name=app_info.display_name,
            running=is_running,
            pids=pids,
            launch_time=launch_time_str,
            window_count=len(pids),  # Approximate
            active_window_title=None,
            cpu_percent=round(total_cpu, 1),
            memory_percent=round(total_mem, 1),
            status="running" if is_running else "stopped",
        )
