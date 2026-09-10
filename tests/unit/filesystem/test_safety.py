"""
Unit tests for sensitivity checking and system path protection.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.safety import SensitivityChecker
from jarvis.filesystem.errors import ProtectedPath, PermissionDenied


def test_sensitive_file_patterns():
    checker = SensitivityChecker()

    assert checker.is_sensitive_file(Path("id_rsa"))
    assert checker.is_sensitive_file(Path(".env"))
    assert checker.is_sensitive_file(Path("db_password.txt"))
    assert checker.is_sensitive_file(Path("user_credentials.json"))
    assert not checker.is_sensitive_file(Path("notes.md"))
    assert not checker.is_sensitive_file(Path("index.html"))


def test_protected_system_paths():
    checker = SensitivityChecker(protected_roots=["C:\\Windows", "/etc"])

    assert checker.is_protected_system_path(Path("C:\\Windows\\System32\\cmd.exe"))
    assert checker.is_protected_system_path(Path("/etc/passwd"))

    with pytest.raises(ProtectedPath):
        checker.check_safety(Path("/etc/passwd"))

    with pytest.raises(PermissionDenied):
        checker.check_safety(Path("server_key.pem"))
