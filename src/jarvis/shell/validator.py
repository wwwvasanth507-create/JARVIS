"""
Command validation, allowlist/denylist policy enforcement, working directory confinement,
and risk tier classification for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from jarvis.filesystem.paths import PathResolver
from jarvis.filesystem.safety import SensitivityChecker
from jarvis.security.permissions import RiskLevel
from jarvis.shell.errors import CommandDenied, InvalidWorkingDirectory
from jarvis.shell.parser import ParsedCommand
from jarvis.shell.safety import DangerousCommandDetector


READ_ONLY_COMMANDS = {
    "python": {"--version", "-v", "-h", "--help"},
    "python3": {"--version", "-v", "-h", "--help"},
    "py": {"--version", "-v", "-h", "--help"},
    "git": {"status", "log", "version", "--version", "diff", "branch"},
    "node": {"--version", "-v", "-h", "--help"},
    "npm": {"--version", "-v", "list"},
    "pip": {"list", "show", "--version"},
    "pip3": {"list", "show", "--version"},
    "pytest": {"--version", "-h", "--help"},
    "echo": set(),
    "dir": set(),
    "ls": set(),
    "pwd": set(),
    "whoami": set(),
    "hostname": set(),
    "ver": set(),
    "uname": set(),
}

NETWORK_AFFECTING_EXECUTABLES = {
    "curl", "wget", "ssh", "scp", "ftp", "ping", "netstat", "telnet", "git"
}

PACKAGE_INSTALL_EXECUTABLES = {
    "pip", "pip3", "npm", "yarn", "pnpm", "apt", "apt-get", "winget", "brew", "choco"
}


class CommandValidator:
    """Validates commands against policy, safe working directory roots, and risk categories."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else Path("config/shell.yaml")
        self.enabled = True
        self.allow_commands: List[str] = [
            "python", "python3", "py", "git", "node", "npm", "pip", "pip3",
            "pytest", "echo", "dir", "ls", "pwd", "whoami", "hostname", "ver", "uname"
        ]
        self.deny_commands: List[str] = ["format", "shutdown", "reboot", "init", "systemctl"]
        self.default_timeout = 30
        self.max_timeout = 300

        self.path_resolver = PathResolver(["./", "~/Documents", "~/Downloads", "~/Desktop"])
        self.sensitivity_checker = SensitivityChecker()

        self._load_config()

    def _load_config(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                sh_cfg = cfg.get("shell", {})
                self.enabled = sh_cfg.get("enabled", True)
                self.allow_commands = sh_cfg.get("allow_commands", self.allow_commands)
                self.deny_commands = sh_cfg.get("deny_commands", self.deny_commands)
                self.default_timeout = sh_cfg.get("default_timeout", self.default_timeout)
                self.max_timeout = sh_cfg.get("max_timeout", self.max_timeout)

    def validate_working_directory(self, target_dir: Optional[Union[str, Path]] = None) -> Path:
        """Validates that working directory exists, is within allowed roots, and is safe."""
        path_obj = Path(target_dir) if target_dir else Path(".")
        try:
            resolved = self.path_resolver.resolve_path(path_obj, check_allowed=True)
            if not resolved.exists() or not resolved.is_dir():
                raise InvalidWorkingDirectory(f"Working directory '{resolved}' does not exist or is not a directory.")
            self.sensitivity_checker.check_safety(resolved)
            return resolved
        except Exception as e:
            raise InvalidWorkingDirectory(f"Invalid shell working directory '{target_dir}': {str(e)}") from e

    def classify_risk(self, parsed: ParsedCommand) -> RiskLevel:
        """Classifies command execution into RiskLevel tiers."""
        exe = parsed.executable.lower()

        # Check read-only fast path
        if exe in READ_ONLY_COMMANDS:
            allowed_sub = READ_ONLY_COMMANDS[exe]
            if not allowed_sub:
                return RiskLevel.LOW
            if parsed.arguments and parsed.arguments[0].lower() in allowed_sub:
                return RiskLevel.LOW

        if exe in PACKAGE_INSTALL_EXECUTABLES:
            return RiskLevel.MEDIUM

        if exe in NETWORK_AFFECTING_EXECUTABLES:
            # git clone or fetch is MEDIUM, network ops
            return RiskLevel.MEDIUM

        if parsed.has_pipeline_operators:
            return RiskLevel.HIGH

        return RiskLevel.MEDIUM

    def validate(self, parsed: ParsedCommand, working_directory: Optional[Union[str, Path]] = None) -> RiskLevel:
        """
        Validates command against policy, safety checks, and allowed executables.
        Returns assessed RiskLevel.
        """
        if not self.enabled:
            raise CommandDenied("Shell subsystem is disabled in configuration.")

        if not parsed.executable:
            raise CommandDenied("Command string cannot be empty.")

        exe = parsed.executable.lower()

        # 1. Check explicit denylist
        if exe in self.deny_commands or parsed.raw_command.lower() in self.deny_commands:
            raise CommandDenied(f"Command '{exe}' is explicitly prohibited by policy (deny_commands).")

        # 2. Check dangerous patterns
        DangerousCommandDetector.inspect(parsed)

        # 3. Check allowlist (if enabled)
        if self.allow_commands and exe not in [cmd.lower() for cmd in self.allow_commands]:
            raise CommandDenied(
                f"Executable '{exe}' is not in configured allow_commands policy list."
            )

        # 4. Validate working directory confinement
        self.validate_working_directory(working_directory)

        # 5. Classify risk level
        return self.classify_risk(parsed)
