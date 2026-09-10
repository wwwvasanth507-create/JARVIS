"""
Unit tests for ModelMemoryChecker.
"""

import pytest
import os
import tempfile
from jarvis.brain.safety import ModelMemoryChecker
from jarvis.brain.errors import ModelMemoryUnavailableError


def test_memory_safety_check_pass():
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(b"0" * 1024 * 1024) # 1 MB file
        tmp_path = tmp.name

    try:
        is_safe, msg = ModelMemoryChecker.check_memory_safety(tmp_path, min_free_ram_gb=0.01)
        assert is_safe is True
        assert "passed" in msg.lower()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_memory_safety_check_fail_exceeded():
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp.write(b"0" * 1024)
        tmp_path = tmp.name

    try:
        # Require impossible 10,000 GB free RAM
        is_safe, msg = ModelMemoryChecker.check_memory_safety(tmp_path, min_free_ram_gb=10000.0)
        assert is_safe is False
        assert "below minimum" in msg.lower()

        with pytest.raises(ModelMemoryUnavailableError):
            ModelMemoryChecker.validate_or_raise(tmp_path, min_free_ram_gb=10000.0)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
