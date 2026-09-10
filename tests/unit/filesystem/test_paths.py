"""
Unit tests for path normalization, resolution, and traversal protection.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.paths import PathResolver
from jarvis.filesystem.errors import InvalidPath, PathOutsideAllowedRoot


def test_path_expansion_and_normalization(tmp_path):
    resolver = PathResolver(allowed_roots=[tmp_path])
    target = tmp_path / "subfolder" / "test.txt"
    resolved = resolver.resolve_path(target, check_allowed=True)
    assert resolved.name == "test.txt"
    assert resolved.is_absolute()


def test_path_traversal_prevention(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    forbidden = tmp_path / "forbidden.txt"
    forbidden.write_text("secret")

    resolver = PathResolver(allowed_roots=[allowed])

    # Attempt ../ escape
    escape_attempt = allowed / ".." / "forbidden.txt"
    with pytest.raises(PathOutsideAllowedRoot):
        resolver.resolve_path(escape_attempt, check_allowed=True)


def test_null_byte_rejection():
    resolver = PathResolver()
    with pytest.raises(InvalidPath):
        resolver.normalize_path("file\0invalid.txt")


def test_reserved_device_name_rejection():
    resolver = PathResolver()
    with pytest.raises(InvalidPath):
        resolver.normalize_path("CON.txt")
    with pytest.raises(InvalidPath):
        resolver.normalize_path("NUL")
