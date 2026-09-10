"""
Safe application launcher with structured arguments, file/URL associations, and working directory validation.
"""

import os
import subprocess
import sys

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jarvis.applications.errors import ApplicationLaunchFailed, ApplicationNotFound
from jarvis.applications.platform import ApplicationPlatform
from jarvis.applications.process import ApplicationProcess
from jarvis.applications.state import ApplicationInfo, LaunchResult
from jarvis.filesystem.paths import PathResolver
from jarvis.filesystem.safety import SensitivityChecker


class ApplicationLauncher:
    """Launches desktop applications safely without raw shell injection."""

    def __init__(self):
        self.path_resolver = PathResolver(["./", "~/Documents", "~/Downloads", "~/Desktop"])
        self.sensitivity_checker = SensitivityChecker()

    def open_application(
        self,
        app_info: ApplicationInfo,
        arguments: Optional[List[str]] = None,
        working_directory: Optional[Union[str, Path]] = None,
    ) -> LaunchResult:
        """Launches application executable directly or via platform default."""
        exec_path = ApplicationPlatform.resolve_executable_path(app_info)
        cmd_executable = str(exec_path) if exec_path else app_info.executable
        cmd_args = [cmd_executable] + (arguments or [])

        work_dir = None
        if working_directory:
            resolved_wd = self.path_resolver.resolve_path(working_directory, check_allowed=True)
            self.sensitivity_checker.check_safety(resolved_wd)
            work_dir = resolved_wd

        try:
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    cmd_args,
                    cwd=work_dir,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                proc = subprocess.Popen(
                    cmd_args,
                    cwd=work_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            return LaunchResult(
                success=True,
                application=app_info.name,
                pid=proc.pid,
                status="started",
                verified=True,
                message=f"Application '{app_info.name}' launched successfully with PID {proc.pid}.",
            )
        except Exception as e:
            raise ApplicationLaunchFailed(f"Failed to launch application '{app_info.name}': {str(e)}") from e

    def open_file(self, app_info: ApplicationInfo, file_path: Union[str, Path]) -> LaunchResult:
        """Opens a document or project path using the target application."""
        resolved_file = self.path_resolver.resolve_path(file_path, check_allowed=True)
        self.sensitivity_checker.check_safety(resolved_file)
        return self.open_application(app_info, arguments=[str(resolved_file)])

    def open_url(self, url_str: str) -> LaunchResult:
        """Opens a web URL using system default browser."""
        if not (url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("file://")):
            raise ValueError("URL scheme must be http, https, or file.")

        try:
            if sys.platform == "win32":
                os.startfile(url_str)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", url_str])
            else:
                subprocess.Popen(["xdg-open", url_str])

            return LaunchResult(
                success=True,
                application="Default Browser",
                pid=None,
                status="started",
                verified=True,
                message=f"Opened URL '{url_str}' in system browser.",
            )
        except Exception as e:
            raise ApplicationLaunchFailed(f"Failed to open URL '{url_str}': {str(e)}") from e
