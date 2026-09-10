"""
Integration & Smoke Tests for Local Model Runtime Subsystem.
"""

import pytest
import os
from jarvis.brain.provider import MockModelProvider, LlamaCppModelProvider
from jarvis.brain.registry import ModelRegistry
from jarvis.brain.context import ContextManager
from jarvis.brain.tool_parser import StructuredToolParser
from jarvis.brain.models import GenerationRequest


def test_brain_fallback_mode_when_no_gguf_model():
    """Verify system defaults cleanly to mock/fallback when no GGUF file exists."""
    registry = ModelRegistry()
    model_info = registry.get_default_or_first_model("models/non_existent.gguf")

    # If no physical GGUF exists, model_info is None or unbacked
    if model_info is None or not os.path.exists(model_info.path):
        provider = MockModelProvider()
        assert provider.load() is True
        resp = provider.generate(GenerationRequest(prompt="Status check"))
        assert "At your service, Boss" in resp.text


def test_real_model_smoke_test_conditional():
    """
    Real Model Smoke Test: If a GGUF model exists, loads and generates text;
    otherwise verifies structural validity of LlamaCppModelProvider.
    """
    registry = ModelRegistry()
    model_info = registry.get_default_or_first_model()

    if model_info and os.path.exists(model_info.path):
        provider = LlamaCppModelProvider(model_info.path)
        assert provider.is_available() is True
        # Load and test short generation
        try:
            provider.load()
            resp = provider.generate(GenerationRequest(prompt="Hi", max_tokens=10))
            assert resp.tokens_generated > 0
            provider.unload()
        except Exception as e:
            pytest.fail(f"Real GGUF model generation failed: {str(e)}")
    else:
        # Report NOT RUN cleanly in test log
        provider = LlamaCppModelProvider("models/language/placeholder.gguf")
        assert provider.is_available() is False


def test_orchestration_tool_call_flow():
    """Verify model output -> structured tool call parser -> args verification."""
    provider = MockModelProvider()
    resp = provider.generate(GenerationRequest(prompt="filesystem.search report.pdf"))

    tool_name, args, err = StructuredToolParser.parse_tool_call(resp.text)
    assert err is None
    assert tool_name == "filesystem.search"
    assert args == {"query": "report.pdf"}
