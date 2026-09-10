"""
Model runtime exception hierarchy for JARVIS.
"""


class ModelError(Exception):
    """Base exception for model runtime errors."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when configured model file cannot be found."""
    pass


class ModelLoadFailedError(ModelError):
    """Raised when model loading fails."""
    pass


class ModelFormatUnsupportedError(ModelError):
    """Raised when model file format is unsupported."""
    pass


class ModelMemoryUnavailableError(ModelError):
    """Raised when loading model would exceed available system RAM."""
    def __init__(self, message: str = "MODEL_MEMORY_UNAVAILABLE"):
        super().__init__(message)


class BackendUnavailableError(ModelError):
    """Raised when model backend (e.g. llama-cpp-python) is unavailable."""
    pass


class GenerationFailedError(ModelError):
    """Raised when text generation fails."""
    pass


class GenerationCancelledError(ModelError):
    """Raised when text generation is cancelled by user/system."""
    pass


class ContextLimitExceededError(ModelError):
    """Raised when context token limit is exceeded."""
    pass


class ToolCallParseError(ModelError):
    """Raised when model output fails to parse into a valid structured tool call."""
    def __init__(self, message: str = "TOOL_CALL_PARSE_ERROR"):
        super().__init__(message)


class ModelHealthCheckFailedError(ModelError):
    """Raised when model health check fails."""
    pass
