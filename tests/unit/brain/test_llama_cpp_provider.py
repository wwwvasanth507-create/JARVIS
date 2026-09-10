"""
Unit tests for LlamaCppModelProvider.
"""

import pytest
from jarvis.brain.provider import LlamaCppModelProvider
from jarvis.brain.errors import ModelNotFoundError, BackendUnavailableError


def test_llama_cpp_missing_model_raises_not_found():
    provider = LlamaCppModelProvider(model_path="non_existent_path.gguf")
    assert provider.is_available() is False

    with pytest.raises(ModelNotFoundError):
        provider.load()
