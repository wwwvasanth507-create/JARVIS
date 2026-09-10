"""
Controlled text and structured file editor module for JARVIS.
"""

import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from pydantic import BaseModel

from jarvis.filesystem.errors import FileTooLarge, PathNotFound, VerificationFailed
from jarvis.filesystem.reader import FileReader
from jarvis.filesystem.writer import FileWriter


class EditOperationResult(BaseModel):
    path: str
    operation: str
    backup_path: Optional[str] = None
    before_sha256: str
    after_sha256: str
    bytes_changed: int
    verified: bool


class FileEditor:
    """Provides controlled target edits, backups, and state diff tracking."""

    def __init__(self, max_edit_size: int = 5242880):  # 5MB edit limit
        self.max_edit_size = max_edit_size
        self.reader = FileReader()

    def create_backup(self, path: Path) -> Path:
        """Creates a timestamped backup copy of path before edit."""
        timestamp = int(time.time())
        backup_path = path.with_suffix(f"{path.suffix}.bak_{timestamp}")
        shutil.copy2(path, backup_path)
        return backup_path

    def edit_file(
        self,
        target_path: Path,
        operation: str,
        target_text: Optional[str] = None,
        replacement_text: Optional[str] = None,
        line_number: Optional[int] = None,
        json_key: Optional[str] = None,
        json_value: Optional[Any] = None,
        create_backup_file: bool = True,
    ) -> EditOperationResult:
        """
        Executes a targeted edit action on target_path.
        Supported operations: 'replace_exact', 'insert_line', 'append_text', 'replace_section', 'edit_json_key'.
        """
        if not target_path.exists():
            raise PathNotFound(f"File '{target_path}' does not exist for editing.")

        file_size = target_path.stat().st_size
        if file_size > self.max_edit_size:
            raise FileTooLarge(f"File size ({file_size} bytes) exceeds edit limit ({self.max_edit_size} bytes).")

        from jarvis.filesystem.metadata import MetadataExtractor
        before_hash = MetadataExtractor.compute_sha256(target_path)

        backup_path_str = None
        if create_backup_file:
            b_path = self.create_backup(target_path)
            backup_path_str = str(b_path.resolve(strict=False))

        read_res = self.reader.read_text_file(target_path)
        content = read_res.content

        new_content = content
        if operation == "replace_exact":
            if not target_text:
                raise ValueError("target_text is required for replace_exact operation.")
            if target_text not in content:
                raise VerificationFailed(f"Target text snippet not found in file '{target_path}'.")
            new_content = content.replace(target_text, replacement_text or "")

        elif operation == "insert_line":
            if line_number is None or line_number < 1:
                raise ValueError("Valid 1-based line_number is required for insert_line.")
            lines = content.splitlines()
            idx = min(line_number - 1, len(lines))
            lines.insert(idx, replacement_text or "")
            new_content = "\n".join(lines)

        elif operation == "append_text":
            new_content = content + ("\n" if content and not content.endswith("\n") else "") + (replacement_text or "")

        elif operation == "edit_json_key":
            if not json_key:
                raise ValueError("json_key is required for edit_json_key operation.")
            try:
                data = json.loads(content)
                data[json_key] = json_value
                new_content = json.dumps(data, indent=2)
            except Exception as e:
                raise VerificationFailed(f"Failed to parse or edit JSON content: {str(e)}") from e

        else:
            raise ValueError(f"Unsupported edit operation '{operation}'.")

        # Atomic write updated content
        write_res = FileWriter.write_file(target_path, new_content, overwrite=True, atomic=True)

        after_hash = write_res.sha256
        if before_hash == after_hash and content != new_content:
            raise VerificationFailed("File content hash remained unchanged after edit operation.")

        return EditOperationResult(
            path=str(target_path.resolve(strict=False)),
            operation=operation,
            backup_path=backup_path_str,
            before_sha256=before_hash,
            after_sha256=after_hash,
            bytes_changed=abs(len(new_content) - len(content)),
            verified=True,
        )
