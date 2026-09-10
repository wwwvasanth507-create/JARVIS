"""
Memory Subsystem Error Hierarchy for JARVIS.
"""


class MemoryError(Exception):
    """Base exception for all memory and knowledge errors."""
    pass


class DatabaseError(MemoryError):
    """Raised when database operation or connection fails."""
    pass


class MemoryNotFoundError(MemoryError):
    """Raised when requested memory item is not found."""
    pass


class PrivacyViolationError(MemoryError):
    """Raised when an attempt to store sensitive information is blocked."""
    def __init__(self, message: str, pattern_matched: str | None = None):
        super().__init__(message)
        self.pattern_matched = pattern_matched


class InvalidMemoryTypeError(MemoryError):
    """Raised when an unsupported memory category is specified."""
    pass
