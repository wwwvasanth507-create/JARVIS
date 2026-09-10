"""
Unit tests for ModelRegistry and discovery.
"""

import pytest
import os
import tempfile
from pathlib import Path
from jarvis.brain.registry import ModelRegistry


def test_model_registry_discovery():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_model = Path(tmp_dir) / "test-model-Q4_K_M.gguf"
        fake_model.write_bytes(b"GGUF_MOCK_DATA")

        registry = ModelRegistry(search_dirs=[tmp_dir])
        models = registry.discover_models()

        assert len(models) == 1
        m = models[0]
        assert m.name == "test-model-Q4_K_M"
        assert m.quantization == "Q4_K_M"
        assert m.format == "GGUF"


def test_model_registry_validation():
    registry = ModelRegistry()
    is_valid, msg = registry.validate_model_path("non_existent_model.gguf")
    assert is_valid is False
    assert "not found" in msg.lower()
