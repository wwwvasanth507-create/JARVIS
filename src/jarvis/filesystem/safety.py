"""
Sensitive path and system boundary detector module for JARVIS.
"""

import fnmatch
from pathlib import Path
from typing import List, Optional, Union
from jarvis.filesystem.errors import ProtectedPath, PermissionDenied


DEFAULT_SENSITIVE_PATTERNS = [
    "*.pem",
    "*.key",
    "*.id_rsa",
    "*.id_ed25519",
    "*.env",
    "*credentials*",
    "*password*",
    "*secret*",
    "*token*",
    "*.kdbx",
    "*.wallet",
    "id_rsa*",
    "id_ed25519*",
    "shadow",
    "passwd",
]

DEFAULT_PROTECTED_ROOTS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "/etc",
    "/usr",
    "/var",
    "/boot",
    "/sys",
    "/proc",
    "/dev",
]


class SensitivityChecker:
    """
    Evaluates whether paths or files target sensitive data or protected system areas.
    """

    def __init__(
        self,
        sensitive_patterns: Optional[List[str]] = None,
        protected_roots: Optional[List[Union[str, Path]]] = None,
    ):
        self.sensitive_patterns = sensitive_patterns or DEFAULT_SENSITIVE_PATTERNS
        self.protected_roots = [
            Path(r).resolve(strict=False) for r in (protected_roots or DEFAULT_PROTECTED_ROOTS)
        ]

    def is_protected_system_path(self, target_path: Path) -> bool:
        """Returns True if path lies inside protected OS root structures."""
        target_resolved = target_path.resolve(strict=False)
        for root in self.protected_roots:
            try:
                target_resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def is_sensitive_file(self, target_path: Path) -> bool:
        """Returns True if filename or path matches known sensitive credentials/secret patterns."""
        basename = target_path.name.lower()
        full_path_str = str(target_path).lower()

        for pattern in self.sensitive_patterns:
            pat_lower = pattern.lower()
            if fnmatch.fnmatch(basename, pat_lower) or fnmatch.fnmatch(full_path_str, f"*{pat_lower}*"):
                return True
        return False

    def check_safety(self, target_path: Path, allow_sensitive: bool = False) -> None:
        """
        Validates path safety. Raises ProtectedPath or PermissionDenied if violated.
        """
        if self.is_protected_system_path(target_path):
            raise ProtectedPath(f"Access to protected system path '{target_path}' is denied.")

        if not allow_sensitive and self.is_sensitive_file(target_path):
            raise PermissionDenied(
                f"Path '{target_path}' is identified as sensitive (credential/secret file). "
                "Explicit authorization required."
            )
