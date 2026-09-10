"""
Custom exceptions for the JARVIS Shell Subsystem.
"""


class ShellError(Exception):
    """Base exception for all shell execution operations in JARVIS."""
    pass


class CommandNotFound(ShellError):
    """Raised when an executable command cannot be located on system PATH."""
    pass


class CommandDenied(ShellError):
    """Raised when a command violates security policy or permission checks."""
    pass


class CommandTimedOut(ShellError):
    """Raised when a command execution exceeds its allotted timeout limit."""
    pass


class CommandCancelled(ShellError):
    """Raised when a running command or background job is cancelled."""
    pass


class InvalidWorkingDirectory(ShellError):
    """Raised when target working directory is non-existent or escapes allowed roots."""
    pass


class DangerousCommandBlocked(ShellError):
    """Raised when a command contains destructive or dangerous operation patterns."""
    pass


class PrivilegeEscalationBlocked(ShellError):
    """Raised when a command attempts unauthorized administrator/sudo escalation."""
    pass


class ProcessNotFound(ShellError):
    """Raised when a specified process PID or handle cannot be found."""
    pass


class JobNotFound(ShellError):
    """Raised when a specified background ShellJob ID is not found."""
    pass


class OutputTruncated(ShellError):
    """Raised or flagged when command output exceeds byte/line bounds."""
    pass


class ShellUnavailable(ShellError):
    """Raised when the shell subsystem is disabled in configuration."""
    pass
