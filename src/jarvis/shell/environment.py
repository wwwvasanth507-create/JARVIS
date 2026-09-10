"""
Platform shell environment detection and secret-redacted environment inspection for JARVIS.
"""

import fnmatch
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


DEFAULT_SENSITIVE_ENV_PATTERNS = [
    "*PASSWORD*",
    "*TOKEN*",
    "*SECRET*",
    "*KEY*",
    "*CREDENTIAL*",
    "*AUTH*",
    "AWS_*",
    "AZURE_*",
    "GCP_*",
]


class ShellInfo(BaseModel):
    platform: str
    shell_name: str
    shell_path: str
    working_directory: str
    available_executables: List[str]


class ShellEnvironment:
    """Manages platform detection, shell paths, and environment variable sanitization."""

    def __init__(self, sensitive_patterns: Optional[List[str]] = None):
        self.sensitive_patterns = sensitive_patterns or DEFAULT_SENSITIVE_ENV_PATTERNS
        self.platform = sys.platform
        self.shell_name, self.shell_path = self._detect_shell()

    def _detect_shell(self) -> tuple[str, str]:
        """Detects primary system shell executable path."""
        if self.platform == "win32":
            pwsh = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
            if pwsh:
                return "PowerShell", pwsh
            cmd = shutil.which("cmd.exe") or "C:\\Windows\\System32\\cmd.exe"
            return "cmd", cmd
        elif self.platform == "darwin":
            zsh = shutil.which("zsh") or "/bin/zsh"
            return "zsh", zsh
        else:
            bash = shutil.which("bash") or "/bin/bash"
            return "bash", bash

    def get_shell_info(self, check_executables: Optional[List[str]] = None) -> ShellInfo:
        """Returns structured metadata regarding local shell capabilities."""
        execs_to_check = check_executables or [
            "python", "python3", "py", "git", "node", "npm", "pip", "pip3", "pytest"
        ]
        available = [e for e in execs_to_check if shutil.which(e) is not None]

        return ShellInfo(
            platform=self.platform,
            shell_name=self.shell_name,
            shell_path=self.shell_path,
            working_directory=str(Path(".").resolve(strict=False)),
            available_executables=available,
        )

    def is_sensitive_variable(self, var_name: str) -> bool:
        """Returns True if an environment variable key matches known sensitive secret patterns."""
        var_upper = var_name.upper()
        for pat in self.sensitive_patterns:
            if fnmatch.fnmatch(var_upper, pat.upper()):
                return True
        return False

    def get_sanitized_environment(self) -> Dict[str, str]:
        """Reads os.environ and redacts sensitive passwords, tokens, and secrets."""
        sanitized = {}
        for k, v in os.environ.items():
            if self.is_sensitive_variable(k):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = v
        return sanitized
