"""
Shell permission evaluator integrating with central JARVIS security framework.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
from jarvis.security.permissions import PermissionCategory, PermissionEvaluator, RiskLevel
from jarvis.shell.errors import CommandDenied, ShellUnavailable
from jarvis.shell.parser import ParsedCommand
from jarvis.shell.validator import CommandValidator


class ShellPermissionChecker:
    """Evaluates permission for shell command execution actions."""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        security_evaluator: Optional[PermissionEvaluator] = None,
    ):
        self.validator = CommandValidator(config_path=config_path)
        self.security_evaluator = security_evaluator or PermissionEvaluator()

    def evaluate_command(
        self,
        parsed: ParsedCommand,
        working_directory: Optional[Union[str, Path]] = None,
    ) -> RiskLevel:
        """
        Validates command safety and evaluates central permission policy.
        Returns assessed RiskLevel.
        """
        risk_level = self.validator.validate(parsed, working_directory=working_directory)

        category = PermissionCategory.RUN_COMMANDS
        if parsed.executable.lower() in {"curl", "wget", "ssh", "scp", "ftp", "ping"}:
            category = PermissionCategory.NETWORK_ACCESS

        sec_result = self.security_evaluator.evaluate(
            category=category,
            risk_level=risk_level,
            action_name=f"shell.execute.{parsed.executable}",
            parameters={
                "command": parsed.raw_command,
                "executable": parsed.executable,
                "arguments": parsed.arguments,
                "working_directory": str(working_directory or "."),
            },
        )

        if not sec_result.allowed:
            raise CommandDenied(sec_result.reason)

        return risk_level
