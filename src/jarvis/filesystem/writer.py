"""
Atomic file creation and writing module for JARVIS.
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel

from jarvis.filesystem.errors import FileExists, PathNotFound, VerificationFailed


class WriteFileResult(BaseModel):
    path: str
    bytes_written: int
    overwritten: bool
    atomic: bool
    verified: bool
    sha256: str


class FileWriter:
    """Handles atomic, safe file writing and creation."""

    @staticmethod
    def write_file(
        target_path: Path,
        content: str,
        overwrite: bool = False,
        encoding: str = "utf-8",
        atomic: bool = True,
    ) -> WriteFileResult:
        """
        Writes content to target_path safely.
        If file exists and overwrite=False, raises FileExists.
        Uses atomic temporary write and replace strategy.
        """
        target_exists = target_path.exists()
        if target_exists and not overwrite:
            raise FileExists(
                f"File '{target_path}' already exists. Overwrite permission required."
            )

        # Ensure parent directory exists
        parent_dir = target_path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        content_bytes = content.encode(encoding)
        bytes_to_write = len(content_bytes)

        if atomic:
            # Atomic write via temporary file
            temp_filename = f".jarvis_tmp_{uuid.uuid4().hex}.tmp"
            temp_path = parent_dir / temp_filename

            try:
                with open(temp_path, "wb") as f:
                    f.write(content_bytes)
                    f.flush()
                    os.fsync(f.fileno())

                # Verify temporary write
                temp_size = temp_path.stat().st_size
                if temp_size != bytes_to_write:
                    raise VerificationFailed(
                        f"Temp write size mismatch: expected {bytes_to_write}, got {temp_size}"
                    )

                # Atomic swap
                os.replace(temp_path, target_path)

            except Exception as e:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass
                raise VerificationFailed(f"Atomic file write failed for '{target_path}': {str(e)}") from e

        else:
            # Non-atomic direct write
            with open(target_path, "wb") as f:
                f.write(content_bytes)

        # Post verification
        if not target_path.exists():
            raise VerificationFailed(f"Target file '{target_path}' does not exist after write.")

        final_size = target_path.stat().st_size
        if final_size != bytes_to_write:
            raise VerificationFailed(
                f"Post-write verification failed: expected {bytes_to_write} bytes, found {final_size} bytes."
            )

        from jarvis.filesystem.metadata import MetadataExtractor
        final_hash = MetadataExtractor.compute_sha256(target_path)

        return WriteFileResult(
            path=str(target_path.resolve(strict=False)),
            bytes_written=bytes_to_write,
            overwritten=target_exists,
            atomic=atomic,
            verified=True,
            sha256=final_hash,
        )
