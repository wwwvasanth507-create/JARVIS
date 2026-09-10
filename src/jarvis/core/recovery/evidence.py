"""
Diagnostic Evidence Collector for JARVIS recovery.
Gathers structured evidence from system subsystems cleanly and cheaply.
"""

import os
import psutil
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DiagnosticEvidence(BaseModel):
    """Structured container for domain-specific evidence."""

    application_state: Optional[Dict[str, Any]] = None
    browser_state: Optional[Dict[str, Any]] = None
    filesystem_state: Optional[Dict[str, Any]] = None
    shell_state: Optional[Dict[str, Any]] = None
    vision_state: Optional[Dict[str, Any]] = None
    model_state: Optional[Dict[str, Any]] = None
    resource_state: Optional[Dict[str, Any]] = None


class EvidenceCollector:
    """Collects evidence safely without collecting sensitive payload data."""

    @staticmethod
    def collect_resource_state() -> Dict[str, Any]:
        """Collects RAM and CPU usage stats."""
        try:
            mem = psutil.virtual_memory()
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "ram_percent": mem.percent,
                "ram_available_mb": round(mem.available / (1024 * 1024), 2),
            }
        except Exception:
            return {"status": "unavailable"}

    @staticmethod
    def collect_filesystem_evidence(path_str: str) -> Dict[str, Any]:
        """Inspects file existence and permissions."""
        if not path_str:
            return {"exists": False, "reason": "empty path"}
        try:
            exists = os.path.exists(path_str)
            is_file = os.path.isfile(path_str) if exists else False
            is_dir = os.path.isdir(path_str) if exists else False
            return {
                "path": path_str,
                "exists": exists,
                "is_file": is_file,
                "is_dir": is_dir,
                "readable": os.access(path_str, os.R_OK) if exists else False,
                "writable": os.access(path_str, os.W_OK) if exists else False,
            }
        except Exception as e:
            return {"path": path_str, "exists": False, "error": str(e)}

    @staticmethod
    def collect_shell_evidence(stderr: Optional[str] = None, exit_code: Optional[int] = None) -> Dict[str, Any]:
        """Inspects shell exit code and error output."""
        return {
            "exit_code": exit_code,
            "stderr_snippet": (stderr or "")[:200],
            "is_timeout": exit_code == -1 or "timed out" in (stderr or "").lower(),
        }
