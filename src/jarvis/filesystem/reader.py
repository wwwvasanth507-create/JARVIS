"""
Safe file reading module with encoding detection, chunking, and line-range support for JARVIS.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel

from jarvis.filesystem.errors import FileTooLarge, PathNotFound, UnsupportedFileType
from jarvis.filesystem.metadata import MetadataExtractor


TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".json", ".jsonl", ".yaml", ".yml",
    ".csv", ".tsv", ".py", ".js", ".ts", ".jsx", ".tsx", ".html",
    ".css", ".xml", ".log", ".sh", ".bat", ".ps1", ".sql", ".ini",
    ".cfg", ".conf", ".toml", ".rst", ".env", ".properties",
}


class ReadFileResult(BaseModel):
    path: str
    content: str
    truncated: bool
    total_bytes: int
    bytes_read: int
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    total_lines: Optional[int] = None
    encoding: str


class FileReader:
    """Reads text files safely with bounds and line slicing."""

    def __init__(self, max_read_bytes: int = 10485760):  # Default 10 MB limit
        self.max_read_bytes = max_read_bytes

    def read_text_file(
        self,
        path: Path,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ) -> ReadFileResult:
        """Reads a file with optional line slicing and byte capping."""
        if not path.exists():
            raise PathNotFound(f"File '{path}' does not exist.")
        if path.is_dir():
            raise UnsupportedFileType(f"Path '{path}' is a directory, not a file.")

        limit_bytes = max_bytes if max_bytes is not None else self.max_read_bytes
        file_size = path.stat().st_size

        # Check if extension is text or attempt text decoding
        ext = path.suffix.lower()
        if ext and ext not in TEXT_EXTENSIONS and file_size > 1048576:
            raise UnsupportedFileType(
                f"File format '{ext}' is not a supported text document format for full reading."
            )

        # Attempt UTF-8 read first, fallback to latin-1
        raw_bytes = None
        encoding_used = "utf-8"
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read(limit_bytes + 1)
        except Exception as e:
            raise UnsupportedFileType(f"Could not read file '{path}': {str(e)}") from e

        truncated_by_bytes = len(raw_bytes) > limit_bytes
        if truncated_by_bytes:
            raw_bytes = raw_bytes[:limit_bytes]

        try:
            decoded_text = raw_bytes.decode("utf-8")
            encoding_used = "utf-8"
        except UnicodeDecodeError:
            try:
                decoded_text = raw_bytes.decode("latin-1")
                encoding_used = "latin-1"
            except Exception as e:
                raise UnsupportedFileType(f"File '{path}' contains non-text binary data.") from e

        lines = decoded_text.splitlines()
        total_lines = len(lines)

        # Line range slicing (1-based)
        truncated_by_lines = False
        selected_lines = lines

        if start_line is not None or end_line is not None:
            s_idx = (start_line - 1) if (start_line and start_line > 0) else 0
            e_idx = end_line if (end_line and end_line > 0) else total_lines
            selected_lines = lines[s_idx:e_idx]
            if len(selected_lines) < total_lines:
                truncated_by_lines = True

        final_content = "\n".join(selected_lines)

        return ReadFileResult(
            path=str(path.resolve(strict=False)),
            content=final_content,
            truncated=(truncated_by_bytes or truncated_by_lines or (file_size > limit_bytes)),
            total_bytes=file_size,
            bytes_read=len(raw_bytes),
            start_line=start_line,
            end_line=end_line,
            total_lines=total_lines,
            encoding=encoding_used,
        )
