"""
Central Application Manager orchestrating discovery, registry, launcher, controller, and permissions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jarvis.applications.controller import ApplicationController
from jarvis.applications.errors import ApplicationError, ApplicationNotFound, AmbiguousApplication
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.permissions import ApplicationPermissionChecker
from jarvis.applications.process import ApplicationProcess
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.state import (
    ApplicationHealth,
    ApplicationInfo,
    ApplicationState,
    ApplicationStartupItem,
    CloseResult,
    LaunchResult,
)


class ApplicationManager:
    """Central entrypoint for safe, permission-evaluated desktop application control."""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        cache_path: Optional[Union[str, Path]] = None,
    ):
        self.registry = ApplicationRegistry(config_path=config_path, cache_path=cache_path)
        self.permission_checker = ApplicationPermissionChecker()
        self.launcher = ApplicationLauncher()
        self.controller = ApplicationController(launcher=self.launcher)

    def list_applications(self) -> List[ApplicationInfo]:
        """Lists registered applications."""
        self.permission_checker.evaluate_action("list")
        return self.registry.list_applications()

    def find_application(self, query: str) -> ApplicationInfo:
        """Resolves application query string or raises AmbiguousApplication / ApplicationNotFound."""
        self.permission_checker.evaluate_action("find", parameters={"query": query})
        return self.registry.resolve(query)

    def open_application(
        self,
        query: str,
        arguments: Optional[List[str]] = None,
        working_directory: Optional[Union[str, Path]] = None,
    ) -> LaunchResult:
        """Resolves and launches application."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("open", app_info=app_info)
        res = self.launcher.open_application(app_info, arguments=arguments, working_directory=working_directory)
        self.controller.wait_until_ready(app_info, timeout=app_info.startup_timeout)
        return res

    def close_application(self, query: str, force: bool = False) -> CloseResult:
        """Resolves and closes application gracefully."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("close", app_info=app_info, parameters={"force": force})
        return self.controller.close_application(app_info, force=force)

    def restart_application(self, query: str) -> LaunchResult:
        """Restarts target application."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("restart", app_info=app_info)
        return self.controller.restart_application(app_info)

    def is_running(self, query: str) -> ApplicationState:
        """Checks running state of target application."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("is_running", app_info=app_info)
        return ApplicationProcess.get_application_state(app_info)

    def list_running(self) -> List[ApplicationState]:
        """Lists state of all registered applications that are currently running."""
        self.permission_checker.evaluate_action("list_running")
        states: List[ApplicationState] = []
        for app_info in self.registry.list_applications():
            st = ApplicationProcess.get_application_state(app_info)
            if st.running:
                states.append(st)
        return states

    def focus_application(self, query: str) -> bool:
        """Focuses application window."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("focus", app_info=app_info)
        return self.controller.focus_application(app_info)

    def check_health(self, query: str) -> ApplicationHealth:
        """Checks health status of target application."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("health", app_info=app_info)
        return self.controller.check_health(app_info)

    def open_file(self, query: str, file_path: Union[str, Path]) -> LaunchResult:
        """Opens a file path using specified application."""
        app_info = self.registry.resolve(query)
        self.permission_checker.evaluate_action("open_file", app_info=app_info, parameters={"file_path": str(file_path)})
        return self.launcher.open_file(app_info, file_path)

    def open_url(self, url_str: str) -> LaunchResult:
        """Opens URL string using system browser."""
        self.permission_checker.evaluate_action("open_url", parameters={"url": url_str})
        return self.launcher.open_url(url_str)

    def list_startup_applications(self) -> List[ApplicationStartupItem]:
        """Read-only inspection of startup items."""
        self.permission_checker.evaluate_action("list_startup")
        return []
