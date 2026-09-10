"""
Post-operation verification module for JARVIS filesystem actions.
"""

from pathlib import Path
from typing import Optional
from jarvis.filesystem.errors import VerificationFailed
from jarvis.filesystem.metadata import MetadataExtractor


class OperationVerifier:
    """Verifies that filesystem state changes actually occurred as requested."""

    @staticmethod
    def verify_exists(path: Path, expect_directory: bool = False) -> bool:
        """Verifies target path exists and matches expected type."""
        if not path.exists():
            raise VerificationFailed(f"Verification Failed: Target path '{path}' does not exist.")
        if expect_directory and not path.is_dir():
            raise VerificationFailed(f"Verification Failed: Path '{path}' exists but is not a directory.")
        if not expect_directory and path.is_dir():
            raise VerificationFailed(f"Verification Failed: Path '{path}' exists but is a directory, not a file.")
        return True

    @staticmethod
    def verify_deleted(path: Path) -> bool:
        """Verifies target path no longer exists."""
        if path.exists():
            raise VerificationFailed(f"Verification Failed: Target path '{path}' still exists after deletion.")
        return True

    @staticmethod
    def verify_copied(source: Path, destination: Path) -> bool:
        """Verifies destination file exists and matches source file size."""
        if not destination.exists():
            raise VerificationFailed(f"Verification Failed: Destination file '{destination}' was not created.")
        if not source.exists():
            raise VerificationFailed(f"Verification Failed: Source file '{source}' missing after copy.")

        src_stat = source.stat()
        dest_stat = destination.stat()

        if src_stat.st_size != dest_stat.st_size:
            raise VerificationFailed(
                f"Verification Failed: Size mismatch after copy (source: {src_stat.st_size}, dest: {dest_stat.st_size})."
            )
        return True

    @staticmethod
    def verify_moved(source: Path, destination: Path) -> bool:
        """Verifies destination exists and source no longer exists."""
        if not destination.exists():
            raise VerificationFailed(f"Verification Failed: Destination '{destination}' does not exist after move.")
        if source.exists():
            raise VerificationFailed(f"Verification Failed: Source path '{source}' still exists after move.")
        return True

    @staticmethod
    def verify_renamed(old_path: Path, new_path: Path) -> bool:
        """Verifies new_path exists and old_path does not."""
        return OperationVerifier.verify_moved(old_path, new_path)
