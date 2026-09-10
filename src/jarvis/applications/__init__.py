"""
JARVIS Application Management Subsystem.
"""

from jarvis.applications.models import ApplicationEntry, ApplicationStatus
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.detector import ApplicationDetector
from jarvis.applications.launcher import ApplicationLauncher

__all__ = [
    "ApplicationEntry",
    "ApplicationStatus",
    "ApplicationRegistry",
    "ApplicationDetector",
    "ApplicationLauncher",
]
