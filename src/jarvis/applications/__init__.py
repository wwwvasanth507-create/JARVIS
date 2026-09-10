"""
JARVIS Application Control & System Integration Package.
"""

from jarvis.applications.manager import ApplicationManager
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.discovery import ApplicationDiscovery
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.controller import ApplicationController
from jarvis.applications.permissions import ApplicationPermissionChecker
from jarvis.applications.process import ApplicationProcess
from jarvis.applications.safety import ApplicationSafety
from jarvis.applications.state import (
    ApplicationInfo,
    ApplicationState,
    ApplicationHealth,
    ApplicationStartupItem,
    LaunchResult,
    CloseResult,
)
from jarvis.applications.errors import (
    ApplicationError,
    ApplicationNotFound,
    ApplicationLaunchFailed,
    ApplicationCloseFailed,
    AmbiguousApplication,
    ApplicationPermissionDenied,
    ApplicationNotRunning,
    ApplicationHealthError,
    ProtectedApplicationBlocked,
    UnsavedWorkWarning,
)

__all__ = [
    "ApplicationManager",
    "ApplicationRegistry",
    "ApplicationDiscovery",
    "ApplicationLauncher",
    "ApplicationController",
    "ApplicationPermissionChecker",
    "ApplicationProcess",
    "ApplicationSafety",
    "ApplicationInfo",
    "ApplicationState",
    "ApplicationHealth",
    "ApplicationStartupItem",
    "LaunchResult",
    "CloseResult",
    "ApplicationError",
    "ApplicationNotFound",
    "ApplicationLaunchFailed",
    "ApplicationCloseFailed",
    "AmbiguousApplication",
    "ApplicationPermissionDenied",
    "ApplicationNotRunning",
    "ApplicationHealthError",
    "ProtectedApplicationBlocked",
    "UnsavedWorkWarning",
]
