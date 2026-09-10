"""
Unit tests for MockModelProvider.
"""

import pytest
from jarvis.brain.provider import MockModelProvider
from jarvis.brain.models import GenerationRequest
from jarvis.brain.errors import GenerationCancelledError


def test_mock_provider_lifecycle():
    provider = MockModelProvider(model_path="mock-model.gguf")
    assert provider.is_ready() is False
    assert provider.load() is True
    assert provider.is_ready() is True

    info = provider.model_info()
    assert info.backend == "mock"
    assert info.name == "Mock GGUF Model"

    health = provider.health_check()
    assert health.available is True
    assert health.loaded is True

    assert provider.unload() is True
    assert provider.is_ready() is False


def test_mock_provider_generate_and_stream():
    provider = MockModelProvider()
    provider.load()

    req = GenerationRequest(prompt="Hello JARVIS", max_tokens=32)
    resp = provider.generate(req)
    assert "At your service, Boss" in resp.text
    assert resp.tokens_generated > 0
    assert resp.duration_seconds >= 0

    # Stream test
    stream_chunks = list(provider.stream(req))
    assert len(stream_chunks) > 0
    assert "".join(stream_chunks).strip() == resp.text.strip()


def test_mock_provider_cancellation():
    provider = MockModelProvider()
    provider.load()
    provider.cancel()

    req = GenerationRequest(prompt="Test cancel")
    with pytest.raises(GenerationCancelledError):
        provider.generate(req)
