"""
Browser Exception Types for JARVIS.
"""


class BrowserError(Exception):
    """Base exception for browser subsystem errors."""
    pass


class NavigationError(BrowserError):
    """Raised when URL navigation fails or is rejected."""
    pass


class TargetNotFoundError(BrowserError):
    """Raised when target element selector cannot be found."""
    pass


class AmbiguousTargetError(BrowserError):
    """Raised when multiple elements match a target selector specification."""
    pass


class DownloadError(BrowserError):
    """Raised when file download fails or violates security policy."""
    pass


class CaptchaDetectedError(BrowserError):
    """Raised when CAPTCHA or anti-bot challenge is detected requiring human intervention."""
    pass


class SecurityViolationError(BrowserError):
    """Raised when browser operation violates security or URL policy."""
    pass
