"""
JARVIS Brain Subsystem: Local LLM Model Runtime & Agent Loop Architecture.
"""

from jarvis.brain.errors import (
    ModelError,
    ModelNotFoundError,
    ModelLoadFailedError,
    ModelFormatUnsupportedError,
    ModelMemoryUnavailableError,
    BackendUnavailableError,
    GenerationFailedError,
    GenerationCancelledError,
    ContextLimitExceededError,
    ToolCallParseError,
    ModelHealthCheckFailedError,
)
from jarvis.brain.models import (
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    ModelHealth,
    PerformanceMode,
    HardwareProfile,
)
from jarvis.brain.provider import (
    ModelProvider,
    MockModelProvider,
    LlamaCppModelProvider,
    MockLocalModelProvider,
)
from jarvis.brain.registry import ModelRegistry
from jarvis.brain.context import ContextManager
from jarvis.brain.tool_parser import StructuredToolParser
from jarvis.brain.safety import ModelMemoryChecker
from jarvis.brain.benchmark import ModelBenchmarkUtility, ModelBenchmark
from jarvis.brain.health import ModelHealthChecker, ModelHealthCheck

__all__ = [
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadFailedError",
    "ModelFormatUnsupportedError",
    "ModelMemoryUnavailableError",
    "BackendUnavailableError",
    "GenerationFailedError",
    "GenerationCancelledError",
    "ContextLimitExceededError",
    "ToolCallParseError",
    "ModelHealthCheckFailedError",
    "ChatMessage",
    "GenerationRequest",
    "GenerationResponse",
    "ModelInfo",
    "ModelHealth",
    "PerformanceMode",
    "HardwareProfile",
    "ModelProvider",
    "MockModelProvider",
    "LlamaCppModelProvider",
    "MockLocalModelProvider",
    "ModelRegistry",
    "ContextManager",
    "StructuredToolParser",
    "ModelMemoryChecker",
    "ModelBenchmarkUtility",
    "ModelBenchmark",
    "ModelHealthChecker",
    "ModelHealthCheck",
]

