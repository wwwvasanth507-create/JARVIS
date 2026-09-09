"""
Unit test suite for JARVIS Local AI Brain & Inference Layer (Prompt 002).
"""

from pathlib import Path
import pytest
from jarvis.brain.provider import (
    ModelProvider,
    MockModelProvider,
    LlamaCppModelProvider,
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
)
from jarvis.brain.registry import ModelRegistry, ModelInfo
from jarvis.brain.context import ContextManager
from jarvis.brain.health import ModelHealthCheck
from jarvis.brain.benchmark import ModelBenchmark


def test_mock_model_provider_lifecycle():
    provider = MockModelProvider(model_path="models/language/mock.gguf")
    assert provider.is_available() is True
    assert provider.initialize() is True
    
    info = provider.model_info()
    assert info["format"] == "GGUF"
    assert info["loaded"] is True

    req = GenerationRequest(prompt="Hello JARVIS")
    resp = provider.generate(req)
    assert isinstance(resp, GenerationResponse)
    assert "At your service, Boss" in resp.text
    assert resp.tokens_generated > 0

    assert provider.unload() is True


def test_mock_model_provider_streaming():
    provider = MockModelProvider()
    req = GenerationRequest(prompt="Status report", stream=True)
    
    chunks = list(provider.stream(req))
    assert len(chunks) > 0
    full_text = "".join(chunks).strip()
    assert "At your service, Boss" in full_text


def test_model_registry_discovery(tmp_path):
    models_dir = tmp_path / "models" / "language"
    models_dir.mkdir(parents=True)
    
    # Create fake GGUF files
    fake_gguf1 = models_dir / "Qwen2.5-3B-Q4_K_M.gguf"
    fake_gguf1.write_bytes(b"GGUF" + b"\x00" * 100)

    fake_gguf2 = models_dir / "Llama-3.2-1B-Q8_0.gguf"
    fake_gguf2.write_bytes(b"GGUF" + b"\x00" * 200)

    registry = ModelRegistry(models_dir=models_dir)
    discovered = registry.discover_models()

    assert len(discovered) == 2
    names = [m.name for m in discovered]
    assert "Qwen2.5-3B-Q4_K_M" in names
    assert "Llama-3.2-1B-Q8_0" in names

    m1 = registry.get_default_or_first_model()
    assert m1 is not None
    assert m1.quantization in ("Q4_K_M", "Q8_0")


def test_missing_model_graceful_handling(tmp_path):
    empty_dir = tmp_path / "empty_models"
    empty_dir.mkdir()

    registry = ModelRegistry(models_dir=empty_dir)
    discovered = registry.discover_models()
    assert len(discovered) == 0

    m = registry.get_default_or_first_model()
    assert m is None

    msg = registry.get_missing_model_message()
    assert "No local language model is configured" in msg
    assert "models/language/" in msg


def test_context_manager_prompt_assembly():
    cm = ContextManager(max_context_tokens=2048)
    assert "JARVIS" in cm.full_system_instruction

    req = cm.build_generation_request(user_prompt="Explain performance mode", temperature=0.3)
    assert isinstance(req, GenerationRequest)
    assert req.temperature == 0.3
    assert len(req.messages) >= 2
    assert req.messages[0].role == "system"
    assert req.messages[-1].role == "user"
    assert req.messages[-1].content == "Explain performance mode"


def test_context_manager_token_budget_trimming():
    cm = ContextManager(max_context_tokens=200)  # Very small context limit
    
    # Create long chat history
    history = [ChatMessage(role="user" if i % 2 == 0 else "assistant", content=f"Long conversation message index {i} with extended text " * 10) for i in range(20)]
    
    req = cm.build_generation_request(user_prompt="Final question", history=history, max_response_tokens=50)
    
    # Verify trimming preserved system prompt and final user prompt
    assert req.messages[0].role == "system"
    assert req.messages[-1].content == "Final question"
    assert len(req.messages) < len(history) + 2


def test_model_health_check():
    provider = MockModelProvider()
    result = ModelHealthCheck.run_check(provider)
    assert result.model_exists is True
    assert result.can_load is True
    assert result.can_generate is True
    assert result.can_unload is True
    assert result.error is None
