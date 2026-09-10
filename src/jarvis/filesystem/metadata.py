"""
File metadata and type identification module for JARVIS.
"""

import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel

from jarvis.filesystem.errors import PathNotFound, InvalidPath


FILE_TYPE_EXTENSIONS = {
    "Text": {".txt", ".log", ".rtf"},
    "Markdown": {".md", ".markdown"},
    "JSON": {".json", ".jsonl"},
    "YAML": {".yaml", ".yml"},
    "CSV": {".csv", ".tsv"},
    "Code": {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".xml",
        ".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".go", ".rs",
        ".sh", ".bat", ".ps1", ".sql", ".toml", ".ini", ".cfg",
    },
    "PDF": {".pdf"},
    "Image": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"},
    "Archive": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"},
    "Executable": {".exe", ".msi", ".dll", ".so", ".dylib", ".app"},
}


class FileMetadata(BaseModel):
    name: str
    path: str
    is_directory: bool
    is_symlink: bool
    type: str
    extension: str
    size: int
    created: str
    modified: str
    accessed: str
    permissions_octal: str
    sha256: Optional[str] = None


class MetadataExtractor:
    """Extracts rich, non-sensitive file and directory metadata."""

    @staticmethod
    def identify_file_type(path: Path) -> str:
        """Determines the semantic category of a file based on extension/attributes."""
        if path.is_dir():
            return "Directory"
        ext = path.suffix.lower()
        for cat, ext_set in FILE_TYPE_EXTENSIONS.items():
            if ext in ext_set:
                return cat
        return "Unknown"

    @classmethod
    def get_metadata(
        cls,
        path: Path,
        calculate_hash: bool = False,
        max_hash_bytes: int = 104857600,  # 100MB limit for hash
    ) -> FileMetadata:
        """Reads metadata for a file or directory."""
        if not path.exists() and not path.is_symlink():
            raise PathNotFound(f"Path '{path}' does not exist.")

        try:
            st = path.stat(follow_symlinks=False)
            is_dir = path.is_dir()
            is_symlink = path.is_symlink()
            size = st.st_size if not is_dir else 0

            # Timestamps
            created_dt = datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat()
            modified_dt = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
            accessed_dt = datetime.fromtimestamp(st.st_atime, tz=timezone.utc).isoformat()

            file_type = cls.identify_file_type(path)
            mode_octal = oct(stat.S_IMODE(st.st_mode))

            sha256_val = None
            if calculate_hash and not is_dir and size <= max_hash_bytes:
                sha256_val = cls.compute_sha256(path)

            return FileMetadata(
                name=path.name,
                path=str(path.resolve(strict=False)),
                is_directory=is_dir,
                is_symlink=is_symlink,
                type=file_type,
                extension=path.suffix.lower(),
                size=size,
                created=created_dt,
                modified=modified_dt,
                accessed=accessed_dt,
                permissions_octal=mode_octal,
                sha256=sha256_val,
            )
        except Exception as e:
            raise InvalidPath(f"Failed to read metadata for '{path}': {str(e)}") from e

    @staticmethod
    def compute_sha256(path: Path, max_bytes: Optional[int] = None) -> str:
        """Computes SHA-256 hash in chunked streams without loading entire file into memory."""
        hasher = hashlib.sha256()
        bytes_read = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                hasher.update(chunk)
                bytes_read += len(chunk)
                if max_bytes and bytes_read >= max_bytes:
                    break
        return hasher.hexdigest()
