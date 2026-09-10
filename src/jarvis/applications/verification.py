"""
Post-execution application state verifier for JARVIS.
"""

import time
from typing import List, Optional
from jarvis.applications.process import ApplicationProcess
from jarvis.applications.state import ApplicationInfo


class ApplicationVerifier:
    """Verifies empirical application state changes after launch or close operations."""

    @staticmethod
    def verify_started(app_info: ApplicationInfo, timeout: float = 5.0) -> tuple[bool, List[int]]:
        """
        Polls until application process starts or timeout expires.
        Returns (success, pids).
        """
        start_t = time.time()
        while (time.time() - start_t) < timeout:
            pids = ApplicationProcess.find_pids_for_executable(app_info.executable)
            if pids:
                return True, pids
            time.sleep(0.3)
        return False, []

    @staticmethod
    def verify_stopped(app_info: ApplicationInfo, timeout: float = 5.0) -> bool:
        """
        Polls until application process terminates or timeout expires.
        Returns True if process is no longer running.
        """
        start_t = time.time()
        while (time.time() - start_t) < timeout:
            pids = ApplicationProcess.find_pids_for_executable(app_info.executable)
            if not pids:
                return True
            time.sleep(0.3)
        return False
