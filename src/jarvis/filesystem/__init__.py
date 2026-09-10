"""
JARVIS Filesystem Management Package.
"""

from jarvis.filesystem.manager import FilesystemManager, DirectoryListResult
from jarvis.filesystem.errors import (
    FilesystemError,
    PathNotFound,
    PermissionDenied,
    PathOutsideAllowedRoot,
    ProtectedPath,
    FileExists,
    DestinationExists,
    InvalidPath,
    UnsupportedFileType,
    FileTooLarge,
    OperationCancelled,
    VerificationFailed,
    FilesystemUnavailable,
)
from jarvis.filesystem.metadata import FileMetadata
from jarvis.filesystem.reader import ReadFileResult
from jarvis.filesystem.writer import WriteFileResult
from jarvis.filesystem.editor import EditOperationResult
from jarvis.filesystem.search import SearchResult
from jarvis.filesystem.duplicates import DuplicateReport
from jarvis.filesystem.storage import StorageInfo
from jarvis.filesystem.organization import OrganizationPlan, OrganizationExecutionReport

__all__ = [
    "FilesystemManager",
    "DirectoryListResult",
    "FilesystemError",
    "PathNotFound",
    "PermissionDenied",
    "PathOutsideAllowedRoot",
    "ProtectedPath",
    "FileExists",
    "DestinationExists",
    "InvalidPath",
    "UnsupportedFileType",
    "FileTooLarge",
    "OperationCancelled",
    "VerificationFailed",
    "FilesystemUnavailable",
    "FileMetadata",
    "ReadFileResult",
    "WriteFileResult",
    "EditOperationResult",
    "SearchResult",
    "DuplicateReport",
    "StorageInfo",
    "OrganizationPlan",
    "OrganizationExecutionReport",
]
