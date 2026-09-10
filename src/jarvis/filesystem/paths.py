"""
Path abstraction, normalization, and path-traversal safety module for JARVIS.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Union
from jarvis.filesystem.errors import InvalidPath, PathOutsideAllowedRoot, ProtectedPath


WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


class PathResolver:
    """
    Handles robust path normalization, resolution, device path detection,
    symlink safety checks, and root confinement validation.
    """

    def __init__(self, allowed_roots: Optional[List[Union[str, Path]]] = None):
        self.allowed_roots: List[Path] = []
        if allowed_roots:
            for root in allowed_roots:
                resolved = self.resolve_path(root, check_allowed=False)
                self.allowed_roots.append(resolved)

    @staticmethod
    def expand_path(raw_path: Union[str, Path]) -> Path:
        """Expands environment variables and user tildes (~)."""
        path_str = str(raw_path)
        # Expand windows %VAR% or unix $VAR
        expanded = os.path.expandvars(os.path.expanduser(path_str))
        return Path(expanded)

    @classmethod
    def normalize_path(cls, raw_path: Union[str, Path]) -> Path:
        """
        Normalizes a path into absolute form, handling traversal and separators.
        Raises InvalidPath if path contains illegal characters or device names.
        """
        path_str = str(raw_path).strip()
        if not path_str:
            raise InvalidPath("Path string cannot be empty.")

        # Check for null bytes or illegal device patterns
        if "\0" in path_str:
            raise InvalidPath("Path contains invalid null byte character.")

        # Windows device paths e.g., \\.\ or \\?\
        if sys.platform == "win32":
            if path_str.startswith(("\\\\.\\", "\\\\?\\", "//./", "//?/")):
                raise InvalidPath(f"Device and raw volume paths are forbidden: {path_str}")

            # Check reserved device filenames (e.g. CON, NUL, AUX)
            base_stem = Path(path_str).stem.upper()
            if base_stem in WINDOWS_RESERVED_NAMES:
                raise InvalidPath(f"Path references reserved Windows device name: {base_stem}")

        expanded = cls.expand_path(raw_path)
        
        try:
            # Resolve to eliminate symlinks and relative components like '..'
            resolved = expanded.resolve(strict=False)
            return resolved
        except Exception as e:
            raise InvalidPath(f"Could not resolve path '{raw_path}': {str(e)}") from e

    def resolve_path(self, raw_path: Union[str, Path], check_allowed: bool = True) -> Path:
        """
        Fully resolves and verifies a path against allowed roots.
        """
        normalized = self.normalize_path(raw_path)

        if check_allowed and self.allowed_roots:
            if not self.is_within_roots(normalized, self.allowed_roots):
                raise PathOutsideAllowedRoot(
                    f"Path '{normalized}' is outside configured allowed root locations."
                )

        return normalized

    @classmethod
    def is_within_roots(cls, target_path: Path, root_paths: List[Path]) -> bool:
        """Checks whether target_path resides within any of the provided root_paths."""
        target_resolved = target_path.resolve(strict=False)
        for root in root_paths:
            root_resolved = root.resolve(strict=False)
            try:
                # relative_to raises ValueError if not a subpath
                target_resolved.relative_to(root_resolved)
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def is_symlink_safe(target_path: Path, allowed_roots: List[Path]) -> bool:
        """
        Verifies that if target_path is a symlink, its target also resolves
        within allowed roots.
        """
        if not target_path.is_symlink():
            return True
        try:
            real_target = target_path.resolve(strict=True)
            return PathResolver.is_within_roots(real_target, allowed_roots)
        except Exception:
            return False
