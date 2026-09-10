"""
Process tree handle tracking and graceful cancellation manager for JARVIS.
"""

import os
import signal
import subprocess
import sys
from typing import Dict, Optional


class JobCanceller:
    """Manages active process handles and provides cross-platform termination."""

    def __init__(self):
        self._active_processes: Dict[str, subprocess.Popen] = {}

    def register_process(self, job_id: str, process: subprocess.Popen) -> None:
        """Registers a running subprocess handle under job_id."""
        self._active_processes[job_id] = process

    def unregister_process(self, job_id: str) -> None:
        """Removes a finished subprocess handle."""
        self._active_processes.pop(job_id, None)

    def cancel_job(self, job_id: str) -> bool:
        """Terminates process associated with job_id."""
        proc = self._active_processes.get(job_id)
        if not proc:
            return False

        try:
            if sys.platform == "win32":
                # Force kill process tree on Windows
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                    timeout=5,
                )
            else:
                # Send SIGTERM then SIGKILL on POSIX
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
            return True
        except Exception:
            return False
        finally:
            self.unregister_process(job_id)
