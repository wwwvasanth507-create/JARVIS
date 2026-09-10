"""
Custom exceptions for the JARVIS Filesystem Subsystem.
"""


class FilesystemError(Exception):
    """Base exception for all filesystem operations in JARVIS."""
    pass


class PathNotFound(FilesystemError):
    """Raised when a requested path does not exist."""
    pass


class PermissionDenied(FilesystemError):
    """Raised when an operation violates permission policies."""
    pass


class PathOutsideAllowedRoot(FilesystemError):
    """Raised when a target path escapes configured allowed root directories."""
    pass


class ProtectedPath(FilesystemError):
    """Raised when an operation targets a critical system or protected location."""
    pass


class FileExists(FilesystemError):
    """Raised when attempting to create a file that already exists without overwrite flag."""
    pass


class DestinationExists(FilesystemError):
    """Raised when target destination already exists during copy/move/rename."""
    pass


class InvalidPath(FilesystemError):
    """Raised when a path string is syntactically invalid or contains illegal characters."""
    pass


class UnsupportedFileType(FilesystemError):
    """Raised when attempting an operation on an unsupported file format."""
    pass


class FileTooLarge(FilesystemError):
    """Raised when a file exceeds size limits for memory or parsing."""
    pass


class OperationCancelled(FilesystemError):
    """Raised when a user or system cancels an in-progress operation."""
    pass


class VerificationFailed(FilesystemError):
    """Raised when post-operation verification fails to confirm expected state change."""
    pass


class FilesystemUnavailable(FilesystemError):
    """Raised when the filesystem subsystem is disabled or unavailable."""
    pass
