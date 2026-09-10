"""
Controlled process inspection and safe process termination manager for JARVIS.
"""

import sys
import psutil
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from jarvis.shell.cancellation import JobCanceller
from jarvis.shell.errors import ProcessNotFound, CommandDenied


SYSTEM_CRITICAL_PROCESSES = {
    "system", "system idle process", "svchost.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "explorer.exe",
    "init", "systemd", "kthreadd"
}


class ProcessInfo(BaseModel):
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: str


class ProcessManager:
    """Safe, non-sensitive process management and termination subsystem."""

    def __init__(self, canceller: Optional[JobCanceller] = None):
        self.canceller = canceller or JobCanceller()

    def list_processes(self, limit: int = 100) -> List[ProcessInfo]:
        """Lists active running processes with safe metadata."""
        procs: List[ProcessInfo] = []
        count = 0
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time']):
            try:
                info = p.info
                create_str = str(info.get('create_time', ''))
                procs.append(
                    ProcessInfo(
                        pid=info['pid'],
                        name=info['name'] or 'unknown',
                        status=info['status'] or 'running',
                        cpu_percent=round(info.get('cpu_percent') or 0.0, 1),
                        memory_percent=round(info.get('memory_percent') or 0.0, 1),
                        create_time=create_str,
                    )
                )
                count += 1
                if count >= limit:
                    break
            except Exception:
                continue
        return procs

    def get_process(self, pid: int) -> ProcessInfo:
        """Inspects a single process by PID."""
        if not psutil.pid_exists(pid):
            raise ProcessNotFound(f"Process PID {pid} does not exist.")
        try:
            p = psutil.Process(pid)
            info = p.as_dict(attrs=['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time'])
            return ProcessInfo(
                pid=info['pid'],
                name=info['name'] or 'unknown',
                status=info['status'] or 'running',
                cpu_percent=round(info.get('cpu_percent') or 0.0, 1),
                memory_percent=round(info.get('memory_percent') or 0.0, 1),
                create_time=str(info.get('create_time', '')),
            )
        except Exception as e:
            raise ProcessNotFound(f"Could not retrieve info for PID {pid}: {str(e)}") from e

    def terminate_process(self, pid: int, force: bool = False) -> bool:
        """Terminates process by PID safely. Protects OS-critical processes."""
        proc_info = self.get_process(pid)
        proc_name_lower = proc_info.name.lower()

        if proc_name_lower in SYSTEM_CRITICAL_PROCESSES:
            raise CommandDenied(
                f"Termination of critical system process '{proc_info.name}' (PID {pid}) is forbidden."
            )

        try:
            p = psutil.Process(pid)
            if force:
                p.kill()
            else:
                p.terminate()
                p.wait(timeout=3)
            return True
        except psutil.TimeoutExpired:
            p.kill()
            return True
        except Exception as e:
            raise CommandDenied(f"Failed to terminate process PID {pid}: {str(e)}") from e
