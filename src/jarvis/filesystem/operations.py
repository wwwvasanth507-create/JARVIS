"""
Single and bulk file operation handlers (copy, move, rename, delete) with verification & rollback tracking.
"""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from jarvis.filesystem.errors import (
    DestinationExists,
    PathNotFound,
    PermissionDenied,
    VerificationFailed,
)
from jarvis.filesystem.verification import OperationVerifier


class RollbackRecord(BaseModel):
    operation_id: str
    operation_type: str
    source_path: str
    destination_path: Optional[str] = None
    timestamp: str
    status: str
    can_rollback: bool


class FileOperations:
    """Handles single and bulk copy, move, rename, delete, and directory creation."""

    def __init__(self):
        self.rollback_log: List[RollbackRecord] = []

    def _record_rollback(
        self,
        op_type: str,
        source: Path,
        destination: Optional[Path] = None,
        can_rollback: bool = True,
    ) -> str:
        op_id = f"op_{uuid.uuid4().hex[:12]}"
        rec = RollbackRecord(
            operation_id=op_id,
            operation_type=op_type,
            source_path=str(source.resolve(strict=False)),
            destination_path=str(destination.resolve(strict=False)) if destination else None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status="completed",
            can_rollback=can_rollback,
        )
        self.rollback_log.append(rec)
        return op_id

    def copy_file(self, source: Path, destination: Path, overwrite: bool = False) -> RollbackRecord:
        """Copies source file to destination safely."""
        if not source.exists():
            raise PathNotFound(f"Source file '{source}' does not exist.")
        if source.is_dir():
            raise ValueError(f"Source '{source}' is a directory. Use copy_directory.")
        if destination.exists() and not overwrite:
            raise DestinationExists(f"Destination '{destination}' already exists.")

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)
        OperationVerifier.verify_copied(source, destination)

        op_id = self._record_rollback("copy", source, destination, can_rollback=True)
        return self.rollback_log[-1]

    def move_file(self, source: Path, destination: Path, overwrite: bool = False) -> RollbackRecord:
        """Moves source file or directory to destination safely."""
        if not source.exists():
            raise PathNotFound(f"Source '{source}' does not exist.")
        if destination.exists() and not overwrite:
            raise DestinationExists(f"Destination '{destination}' already exists.")

        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source), str(destination))
        OperationVerifier.verify_moved(source, destination)

        op_id = self._record_rollback("move", source, destination, can_rollback=True)
        return self.rollback_log[-1]

    def rename_file(self, target: Path, new_name: str) -> RollbackRecord:
        """Renames a file or directory within its parent folder."""
        if not target.exists():
            raise PathNotFound(f"Target '{target}' does not exist.")

        destination = target.parent / new_name
        if destination.exists():
            raise DestinationExists(f"Target destination filename '{new_name}' already exists.")

        target.rename(destination)
        OperationVerifier.verify_renamed(target, destination)

        op_id = self._record_rollback("rename", target, destination, can_rollback=True)
        return self.rollback_log[-1]

    def create_directory(self, target_path: Path, exist_ok: bool = True) -> RollbackRecord:
        """Creates a directory structure."""
        if target_path.exists() and not exist_ok:
            raise DestinationExists(f"Directory '{target_path}' already exists.")

        target_path.mkdir(parents=True, exist_ok=exist_ok)
        OperationVerifier.verify_exists(target_path, expect_directory=True)

        op_id = self._record_rollback("create_directory", target_path, can_rollback=False)
        return self.rollback_log[-1]

    def delete_file(self, target: Path) -> RollbackRecord:
        """Deletes a single file safely."""
        if not target.exists():
            raise PathNotFound(f"Target file '{target}' does not exist.")
        if target.is_dir():
            raise ValueError(f"Target '{target}' is a directory. Use delete_directory.")

        target.unlink()
        OperationVerifier.verify_deleted(target)

        op_id = self._record_rollback("delete_file", target, can_rollback=False)
        return self.rollback_log[-1]

    def delete_directory(self, target: Path, recursive: bool = False) -> RollbackRecord:
        """Deletes a directory (empty by default, or recursively if approved)."""
        if not target.exists():
            raise PathNotFound(f"Target directory '{target}' does not exist.")
        if not target.is_dir():
            raise ValueError(f"Target '{target}' is a file, not a directory.")

        if recursive:
            shutil.rmtree(target)
        else:
            target.rmdir()  # Fails if non-empty

        OperationVerifier.verify_deleted(target)

        op_id = self._record_rollback("delete_directory", target, can_rollback=False)
        return self.rollback_log[-1]
