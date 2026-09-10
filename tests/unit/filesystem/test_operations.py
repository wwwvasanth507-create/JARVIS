"""
Unit tests for single and bulk file operations (copy, move, rename, delete, storage info).
"""

import pytest
from pathlib import Path
from jarvis.filesystem.operations import FileOperations
from jarvis.filesystem.storage import StorageInfoProvider
from jarvis.filesystem.errors import DestinationExists, PathNotFound, VerificationFailed


def test_copy_move_rename_delete_operations(tmp_path):
    ops = FileOperations()

    # Create source file
    src = tmp_path / "source.txt"
    src.write_text("JARVIS test content")

    # 1. Copy
    copy_dst = tmp_path / "copy.txt"
    rec_copy = ops.copy_file(src, copy_dst)
    assert copy_dst.exists()
    assert copy_dst.read_text() == "JARVIS test content"
    assert rec_copy.status == "completed"

    # 2. Rename
    rec_rename = ops.rename_file(copy_dst, "renamed.txt")
    renamed_dst = tmp_path / "renamed.txt"
    assert renamed_dst.exists()
    assert not copy_dst.exists()

    # 3. Move
    move_dst = tmp_path / "subfolder" / "moved.txt"
    rec_move = ops.move_file(renamed_dst, move_dst)
    assert move_dst.exists()
    assert not renamed_dst.exists()

    # 4. Delete
    rec_delete = ops.delete_file(move_dst)
    assert not move_dst.exists()


def test_storage_info():
    info = StorageInfoProvider.get_storage_info(Path("."))
    assert info.total_bytes > 0
    assert info.free_bytes > 0
    assert 0.0 <= info.percent_used <= 100.0
