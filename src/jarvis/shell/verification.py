"""
Post-execution empirical command verification module for JARVIS.
"""

import re
from pathlib import Path
from typing import Optional, Union
from jarvis.filesystem.verification import OperationVerifier
from jarvis.shell.result import CommandResult


class CommandVerifier:
    """Verifies that command execution achieved its intended outcome."""

    @staticmethod
    def verify_result(
        result: CommandResult,
        expected_output_pattern: Optional[str] = None,
        expected_artifact_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """
        Verifies command execution.
        Returns True if exit code is 0, expected output pattern matches,
        and expected artifact exists.
        """
        if result.exit_code != 0 or result.timed_out or result.cancelled:
            return False

        if expected_output_pattern:
            combined = f"{result.stdout}\n{result.stderr}"
            if not re.search(expected_output_pattern, combined, re.IGNORECASE):
                return False

        if expected_artifact_path:
            p = Path(expected_artifact_path)
            try:
                OperationVerifier.verify_exists(p)
            except Exception:
                return False

        return True
