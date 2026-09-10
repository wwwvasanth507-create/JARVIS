"""
JARVIS Controlled Shell & Terminal Package.
"""

from jarvis.shell.manager import ShellManager
from jarvis.shell.errors import (
    ShellError,
    CommandNotFound,
    CommandDenied,
    CommandTimedOut,
    CommandCancelled,
    InvalidWorkingDirectory,
    DangerousCommandBlocked,
    PrivilegeEscalationBlocked,
    ProcessNotFound,
    JobNotFound,
    OutputTruncated,
    ShellUnavailable,
)
from jarvis.shell.result import CommandRequest, CommandResult, AuditRecord
from jarvis.shell.executor import ShellJob
from jarvis.shell.environment import ShellInfo
from jarvis.shell.processes import ProcessInfo

__all__ = [
    "ShellManager",
    "ShellError",
    "CommandNotFound",
    "CommandDenied",
    "CommandTimedOut",
    "CommandCancelled",
    "InvalidWorkingDirectory",
    "DangerousCommandBlocked",
    "PrivilegeEscalationBlocked",
    "ProcessNotFound",
    "JobNotFound",
    "OutputTruncated",
    "ShellUnavailable",
    "CommandRequest",
    "CommandResult",
    "AuditRecord",
    "ShellJob",
    "ShellInfo",
    "ProcessInfo",
]
