"""
Model Provider Abstraction & Local Inference Runtime Interface for JARVIS.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
import time
import os
from pathlib import Path

from jarvis.brain.models import (
    ChatMessage, GenerationRequest, GenerationResponse, ModelInfo, ModelHealth
)
from jarvis.brain.errors import (
    ModelError, ModelNotFoundError, ModelLoadFailedError,
    ModelMemoryUnavailableError, BackendUnavailableError, GenerationFailedError, GenerationCancelledError
)
from jarvis.brain.safety import ModelMemoryChecker


class ModelProvider(ABC):
    """Abstract Base Class for all JARVIS Model Providers."""

    def __init__(self, model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.model_path = model_path
        self.config = config or {}
        self._is_loaded = False
        self._last_error: Optional[str] = None
        self._cancel_requested = False

    @abstractmethod
    def load(self) -> bool:
        """Loads model into RAM."""
        pass

    def initialize(self) -> bool:
        """Alias for load()."""
        return self.load()

    @abstractmethod
    def unload(self) -> bool:
        """Unloads model from RAM."""
        pass

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generates a non-streaming text completion."""
        pass

    @abstractmethod
    def stream(self, request: GenerationRequest) -> Generator[str, None, GenerationResponse]:
        """Streams generated tokens line-by-line or token-by-token."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if model file exists and dependencies are available."""
        pass

    def is_ready(self) -> bool:
        """Returns True if model is loaded into memory and ready for generation."""
        return self._is_loaded

    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Returns metadata about the active model."""
        pass

    def health_check(self) -> ModelHealth:
        """Returns status health of the model runtime."""
        info = self.model_info()
        est_mb = round(os.path.getsize(self.model_path) / (1024 * 1024), 2) if self.model_path and os.path.exists(self.model_path) else 0.0
        return ModelHealth(
            available=self.is_available(),
            loaded=self._is_loaded,
            backend=info.backend,
            model=info.name,
            context_size=self.config.get("context_size", 2048),
            threads=self.config.get("threads", 4) if isinstance(self.config.get("threads"), int) else 4,
            gpu_layers=self.config.get("gpu_layers", 0),
            memory_estimate_mb=est_mb,
            last_error=self._last_error
        )

    def cancel(self) -> None:
        """Signals active generation to cancel."""
        self._cancel_requested = True



class MockModelProvider(ModelProvider):
    """Fast, deterministic Mock Model Provider for unit testing without GGUF binaries."""

    def __init__(self, model_path: str = "models/language/mock-model.gguf", config: Optional[Dict[str, Any]] = None):
        super().__init__(model_path, config)

    def load(self) -> bool:
        self._is_loaded = True
        return True

    def is_available(self) -> bool:
        return True

    def unload(self) -> bool:
        self._is_loaded = False
        return True

    def model_info(self) -> ModelInfo:
        return ModelInfo(
            name="Mock GGUF Model",
            path=self.model_path or "mock-model.gguf",
            size_bytes=1024*1024,
            size_mb=1.0,
            format="GGUF",
            quantization="Q4_K_M",
            backend="mock",
            available=True,
            loaded=self._is_loaded
        )

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if self._cancel_requested:
            self._cancel_requested = False
            raise GenerationCancelledError("Generation was cancelled.")

        if not self._is_loaded:
            self.load()

        start = time.perf_counter()
        prompt_text = request.prompt or (request.messages[-1].content if request.messages else "Hello")

        # Check for tool test keywords
        if "filesystem.search" in prompt_text or "search files" in prompt_text:
            response_text = '{"tool": "filesystem.search", "arguments": {"query": "report.pdf"}}'
        else:
            response_text = f"At your service, Boss. Processed request: '{prompt_text}'."

        duration = time.perf_counter() - start
        tokens = len(response_text.split())

        return GenerationResponse(
            text=response_text,
            finish_reason="stop",
            tokens_generated=tokens,
            duration_seconds=round(duration, 4),
            tokens_per_second=round(tokens / max(0.001, duration), 2),
            model_name="Mock GGUF Model",
        )

    def stream(self, request: GenerationRequest) -> Generator[str, None, GenerationResponse]:
        if not self._is_loaded:
            self.load()

        start = time.perf_counter()
        prompt_text = request.prompt or (request.messages[-1].content if request.messages else "Hello")
        full_text = f"At your service, Boss. Processed request: '{prompt_text}'."

        words = full_text.split()
        accumulated = []
        for word in words:
            if self._cancel_requested:
                self._cancel_requested = False
                raise GenerationCancelledError("Generation streaming was cancelled.")
            chunk = word + " "
            accumulated.append(chunk)
            yield chunk

        duration = time.perf_counter() - start
        final_text = "".join(accumulated).strip()
        tokens = len(words)

        return GenerationResponse(
            text=final_text,
            finish_reason="stop",
            tokens_generated=tokens,
            duration_seconds=round(duration, 4),
            tokens_per_second=round(tokens / max(0.001, duration), 2),
            model_name="Mock GGUF Model",
        )


# Aliases for backward compatibility
MockLocalModelProvider = MockModelProvider
ModelGenerationRequest = GenerationRequest
ModelGenerationResponse = GenerationResponse


class LlamaCppModelProvider(ModelProvider):
    """
    Native llama.cpp local inference provider using llama-cpp-python binding.
    Executes GGUF quantized models on CPU with zero cloud API dependencies.
    """

    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(model_path, config)
        self._llm = None

    def is_available(self) -> bool:
        if not self.model_path:
            return False
        p = Path(self.model_path)
        return p.exists() and p.is_file()

    def load(self) -> bool:
        if self._is_loaded and self._llm is not None:
            return True

        if not self.is_available():
            err = f"Local GGUF model file not found at '{self.model_path}'."
            self._last_error = err
            raise ModelNotFoundError(err)

        # Memory safety check
        min_free_ram = self.config.get("min_free_ram_gb", 1.5)
        headroom = self.config.get("ram_headroom_factor", 1.2)
        ModelMemoryChecker.validate_or_raise(self.model_path, min_free_ram_gb=min_free_ram, headroom_factor=headroom)

        threads = self.config.get("threads", 4)
        if isinstance(threads, str) and threads == "auto":
            try:
                from jarvis.system.hardware import HardwareDetector
                profile = HardwareDetector.detect()
                threads = max(1, profile.physical_cores - 1)
            except Exception:
                threads = max(1, (os.cpu_count() or 4) - 1)

        try:
            import importlib
            llama_mod = importlib.import_module("llama_cpp")
            Llama = getattr(llama_mod, "Llama")
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("context_size", 2048),
                n_threads=threads,
                n_batch=self.config.get("batch_size", 512),
                n_gpu_layers=self.config.get("gpu_layers", 0),
                use_mmap=self.config.get("use_mmap", True),
                use_mlock=self.config.get("use_mlock", False),
                verbose=self.config.get("verbose", False),
            )
            self._is_loaded = True
            self._last_error = None
            return True
        except ImportError:
            err = "Package 'llama-cpp-python' is not installed. Run 'pip install llama-cpp-python' for local GGUF model inference."
            self._last_error = err
            raise BackendUnavailableError(err)
        except Exception as e:
            err = f"Failed to initialize llama.cpp model from '{self.model_path}': {str(e)}"
            self._last_error = err
            raise ModelLoadFailedError(err)

    def unload(self) -> bool:
        if self._llm is not None:
            del self._llm
            self._llm = None
        self._is_loaded = False
        return True

    def model_info(self) -> ModelInfo:
        path_obj = Path(self.model_path) if self.model_path else None
        size_b = path_obj.stat().st_size if path_obj and path_obj.exists() else 0
        return ModelInfo(
            name=path_obj.name if path_obj else "Unknown",
            path=self.model_path or "",
            size_bytes=size_b,
            size_mb=round(size_b / (1024 * 1024), 2),
            format="GGUF",
            context_size=self.config.get("context_size", 2048),
            quantization="Q4_K_M" if "Q4_K_M" in (self.model_path or "") else "Unknown",
            backend="llama.cpp",
            available=self.is_available(),
            loaded=self._is_loaded
        )

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if self._cancel_requested:
            self._cancel_requested = False
            raise GenerationCancelledError("Generation was cancelled.")

        if not self._is_loaded:
            self.load()

        start = time.perf_counter()
        prompt_text = request.prompt or ""
        if not prompt_text and request.messages:
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

        try:
            raw_output = self._llm(
                prompt_text,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences or None,
            )
            duration = time.perf_counter() - start
            text = raw_output["choices"][0]["text"]
            tokens = raw_output.get("usage", {}).get("completion_tokens", len(text.split()))

            return GenerationResponse(
                text=text,
                finish_reason=raw_output["choices"][0].get("finish_reason", "stop"),
                tokens_generated=tokens,
                duration_seconds=round(duration, 4),
                tokens_per_second=round(tokens / max(0.001, duration), 2),
                model_name=self.model_info().name,
                raw_response=raw_output,
            )
        except Exception as e:
            raise GenerationFailedError(f"Local LLM generation failed: {str(e)}")

    def stream(self, request: GenerationRequest) -> Generator[str, None, GenerationResponse]:
        if not self._is_loaded:
            self.load()

        start = time.perf_counter()
        prompt_text = request.prompt or ""
        if not prompt_text and request.messages:
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

        try:
            stream_iter = self._llm(
                prompt_text,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                stop=request.stop_sequences or None,
                stream=True,
            )

            collected_text = []
            tokens = 0
            for chunk in stream_iter:
                if self._cancel_requested:
                    self._cancel_requested = False
                    raise GenerationCancelledError("Generation streaming was cancelled.")
                delta = chunk["choices"][0]["text"]
                collected_text.append(delta)
                tokens += 1
                yield delta

            duration = time.perf_counter() - start
            final_text = "".join(collected_text)

            return GenerationResponse(
                text=final_text,
                finish_reason="stop",
                tokens_generated=tokens,
                duration_seconds=round(duration, 4),
                tokens_per_second=round(tokens / max(0.001, duration), 2),
                model_name=self.model_info().name,
            )
        except GenerationCancelledError:
            raise
        except Exception as e:
            raise GenerationFailedError(f"Local LLM streaming generation failed: {str(e)}")
