"""
Screen Understanding, OCR & Vision exception hierarchy for JARVIS.
"""


class VisionError(Exception):
    """Base exception for vision subsystem errors."""
    pass


class ScreenCaptureUnavailableError(VisionError):
    """Raised when screen capture fails or is unsupported on host system."""
    pass


class OCRUnavailableError(VisionError):
    """Raised when local OCR dependencies are missing or uninitialized."""
    pass


class VisionModelUnavailableError(VisionError):
    """Raised when local vision model is unavailable or fails to load."""
    pass


class ScreenPrivacyDeniedError(VisionError):
    """Raised when screen analysis is blocked by privacy policy exclusions."""
    def __init__(self, message: str = "SCREEN_PRIVACY_DENIED"):
        super().__init__(message)


class VisualTargetNotFoundError(VisionError):
    """Raised when requested visual target is not found on screen."""
    def __init__(self, message: str = "VISUAL_TARGET_NOT_FOUND"):
        super().__init__(message)


class AmbiguousVisualTargetError(VisionError):
    """Raised when multiple matching visual targets are detected."""
    def __init__(self, message: str = "AMBIGUOUS_VISUAL_TARGET"):
        super().__init__(message)


class VisionAnalysisTimeoutError(VisionError):
    """Raised when visual analysis exceeds configured timeout."""
    pass


class VisionVerificationFailedError(VisionError):
    """Raised when visual state verification fails after an action."""
    pass
