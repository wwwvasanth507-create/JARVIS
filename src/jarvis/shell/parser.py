"""
Command string parsing, argument tokenization, and operator detection for JARVIS.
"""

import shlex
import sys
from typing import List, Optional, Set
from pydantic import BaseModel


PIPELINE_OPERATORS: Set[str] = {"|", ">", ">>", "<", "&&", "||", ";", "&"}


class ParsedCommand(BaseModel):
    raw_command: str
    executable: str
    arguments: List[str]
    has_pipeline_operators: bool
    operators_found: List[str]


class CommandParser:
    """Parses command strings into structured tokens and detects shell composition operators."""

    @staticmethod
    def _strip_quotes(token: str) -> str:
        """Removes enclosing single or double quotes from a token."""
        t = token.strip()
        if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
            return t[1:-1]
        return t

    @classmethod
    def parse(cls, command_str: str) -> ParsedCommand:
        """Parses a command string into executable and argument tokens."""
        cmd_trimmed = command_str.strip()
        if not cmd_trimmed:
            return ParsedCommand(
                raw_command="",
                executable="",
                arguments=[],
                has_pipeline_operators=False,
                operators_found=[],
            )

        # Detect operators in raw string before shlex splitting
        operators_found = []
        for op in PIPELINE_OPERATORS:
            if f" {op} " in f" {cmd_trimmed} " or cmd_trimmed.startswith(f"{op} ") or cmd_trimmed.endswith(f" {op}"):
                operators_found.append(op)

        # Tokenize using posix=True to ensure quotes around argument strings are stripped
        try:
            tokens = shlex.split(cmd_trimmed, posix=True)
        except Exception:
            tokens = [cls._strip_quotes(t) for t in cmd_trimmed.split()]

        if not tokens:
            executable = ""
            args = []
        else:
            executable = tokens[0]
            args = [cls._strip_quotes(t) for t in tokens[1:]]

        return ParsedCommand(
            raw_command=cmd_trimmed,
            executable=executable,
            arguments=args,
            has_pipeline_operators=len(operators_found) > 0,
            operators_found=operators_found,
        )
