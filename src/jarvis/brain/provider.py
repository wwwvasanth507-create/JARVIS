"""
Model Provider Abstraction & Local Inference Runtime Interface for JARVIS.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
import time
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant")
    content: str = Field(..., description="Text content")


class GenerationRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.2
    top_p: float = 0.95
    max_tokens: int = 512
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = False


class GenerationResponse(BaseModel):
    text: str
    finish_reason: str = "stop"
    tokens_generated: int = 0
    duration_seconds: float = 0.0
    tokens_per_second: float = 0.0
    model_name: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class ModelProvider(ABC):
    """Abstract Base Class for all JARVIS Model Providers."""

    def __init__(self, model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.model_path = model_path
        self.config = config or {}
        self._is_loaded = False

    @abstractmethod
    def initialize(self) -> bool:
        """Loads model into memory."""
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
    def unload(self) -> bool:
        """Unloads model from RAM."""
        pass

    @abstractmethod
    def model_info(self) -> Dict[str, Any]:
        """Returns metadata about the active model."""
        pass


class MockModelProvider(ModelProvider):
    """Fast, deterministic Mock Model Provider for unit testing without GGUF binaries."""

    def __init__(self, model_path: str = "mock-model.gguf", config: Optional[Dict[str, Any]] = None):
        super().__init__(model_path, config)

    def initialize(self) -> bool:
        self._is_loaded = True
        return True

    def is_available(self) -> bool:
        return True

    def unload(self) -> bool:
        self._is_loaded = False
        return True

    def model_info(self) -> Dict[str, Any]:
        return {
            "name": "Mock GGUF Model",
            "path": self.model_path,
            "format": "GGUF",
            "quantization": "Q4_K_M",
            "backend": "mock",
            "loaded": self._is_loaded,
        }

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._is_loaded:
            self.initialize()

        start = time.perf_counter()
        prompt_text = request.prompt or (request.messages[-1].content if request.messages else "Hello")
        
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
            self.initialize()

        start = time.perf_counter()
        prompt_text = request.prompt or (request.messages[-1].content if request.messages else "Hello")
        full_text = f"At your service, Boss. Processed request: '{prompt_text}'."
        
        words = full_text.split()
        accumulated = []
        for word in words:
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


# Backward compatibility aliases
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
        from pathlib import Path
        p = Path(self.model_path)
        return p.exists() and p.is_file()

    def initialize(self) -> bool:
        if self._is_loaded and self._llm is not None:
            return True

        if not self.is_available():
            raise FileNotFoundError(f"Local GGUF model file not found at '{self.model_path}'.")

        threads = self.config.get("threads", 4)
        if isinstance(threads, str) and threads == "auto":
            from jarvis.system.hardware import HardwareDetector
            profile = HardwareDetector.detect()
            threads = max(1, profile.physical_cores - 1)

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
            return True
        except ImportError:
            raise ImportError(
                "Package 'llama-cpp-python' is not installed. Run 'pip install llama-cpp-python' for local GGUF model inference."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize llama.cpp model from '{self.model_path}': {str(e)}")

    def unload(self) -> bool:
        if self._llm is not None:
            del self._llm
            self._llm = None
        self._is_loaded = False
        return True

    def model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_path.split("/")[-1] if self.model_path else "Unknown",
            "path": self.model_path,
            "format": "GGUF",
            "loaded": self._is_loaded,
            "backend": "llama.cpp",
        }

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._is_loaded:
            self.initialize()

        start = time.perf_counter()
        prompt_text = request.prompt or ""
        if not prompt_text and request.messages:
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

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
            model_name=self.model_info()["name"],
            raw_response=raw_output,
        )

    def stream(self, request: GenerationRequest) -> Generator[str, None, GenerationResponse]:
        if not self._is_loaded:
            self.initialize()

        start = time.perf_counter()
        prompt_text = request.prompt or ""
        if not prompt_text and request.messages:
            prompt_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])

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
            model_name=self.model_info()["name"],
        )
