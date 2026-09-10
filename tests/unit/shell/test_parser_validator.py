"""
Unit tests for command parsing, tokenization, allowlist/denylist validation, and working directory safety.
"""

import pytest
from pathlib import Path
from jarvis.security.permissions import RiskLevel
from jarvis.shell.parser import CommandParser
from jarvis.shell.validator import CommandValidator
from jarvis.shell.errors import CommandDenied, InvalidWorkingDirectory


def test_command_parser_tokenization():
    parsed = CommandParser.parse("python script.py --name 'John Doe'")
    assert parsed.executable == "python"
    assert parsed.arguments == ["script.py", "--name", "John Doe"]
    assert not parsed.has_pipeline_operators


def test_command_parser_operator_detection():
    parsed = CommandParser.parse("cat file.txt | grep error > output.log")
    assert parsed.executable == "cat"
    assert parsed.has_pipeline_operators
    assert "|" in parsed.operators_found
    assert ">" in parsed.operators_found


def test_command_validator_allowlist_and_denylist(tmp_path):
    validator = CommandValidator()
    validator.path_resolver.allowed_roots = [tmp_path.resolve(strict=False)]

    # Allowed command
    parsed_git = CommandParser.parse("git status")
    risk = validator.validate(parsed_git, working_directory=tmp_path)
    assert risk == RiskLevel.LOW

    # Denied command
    parsed_shutdown = CommandParser.parse("shutdown /s /t 0")
    with pytest.raises(CommandDenied):
        validator.validate(parsed_shutdown, working_directory=tmp_path)


def test_working_directory_confinement(tmp_path):
    validator = CommandValidator()
    validator.path_resolver.allowed_roots = [tmp_path]

    # Non-existent working directory
    with pytest.raises(InvalidWorkingDirectory):
        validator.validate_working_directory(tmp_path / "non_existent_folder")
