"""
End-to-end safe integration test for JARVIS Filesystem Subsystem.
Operates exclusively within an isolated temporary test directory.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.manager import FilesystemManager


def test_safe_filesystem_integration_lifecycle(tmp_path):
    """
    Executes a complete 13-step isolated filesystem lifecycle test.
    Never accesses or modifies real user files.
    """
    # 1. Initialize manager configured exclusively for isolated tmp_path
    mgr = FilesystemManager()
    mgr.permission_checker.allow_delete = True  # Enable deletion for test environment
    mgr.permission_checker.path_resolver.allowed_roots = [tmp_path.resolve(strict=False)]

    # 2. Create sample files
    file_1 = tmp_path / "sample_notes.md"
    file_1_content = "# Project Notes\n- CPU-first local agent\n- Safe filesystem operations"
    mgr.create_file(file_1, content=file_1_content)

    # 3. List directory
    list_res = mgr.list_directory(tmp_path)
    assert list_res.total_entries == 1
    assert list_res.entries[0].name == "sample_notes.md"

    # 4. Read one file
    read_res = mgr.read_file(file_1)
    assert read_res.content == file_1_content
    assert not read_res.truncated

    # 5. Create another file
    file_2 = tmp_path / "config.json"
    mgr.create_file(file_2, content='{"status": "draft", "version": 1}')

    # 6. Edit file (JSON key edit)
    edit_res = mgr.edit_file(
        file_2,
        operation="edit_json_key",
        json_key="status",
        json_value="verified",
        create_backup=False,
    )
    assert edit_res.verified
    updated_read = mgr.read_file(file_2)
    assert '"status": "verified"' in updated_read.content

    # 7. Copy file
    copy_dest = tmp_path / "config_copy.json"
    mgr.copy_file(file_2, copy_dest)
    assert copy_dest.exists()

    # 8. Rename file
    mgr.rename_file(copy_dest, "config_renamed.json")
    renamed_path = tmp_path / "config_renamed.json"
    assert renamed_path.exists()
    assert not copy_dest.exists()

    # 9. Move file into subfolder
    subfolder = tmp_path / "archive"
    mgr.create_directory(subfolder)
    mgr.move_file(renamed_path, subfolder / "config_renamed.json")
    moved_path = subfolder / "config_renamed.json"
    assert moved_path.exists()

    # 10. Search for files
    search_res = mgr.search_files(tmp_path, extension=".json")
    assert search_res.total_found == 2  # config.json and archive/config_renamed.json

    # 11. Verify metadata & storage
    meta = mgr.get_metadata(file_1, calculate_hash=True)
    assert meta.type == "Markdown"
    assert meta.sha256 is not None

    storage = mgr.get_storage_info(tmp_path)
    assert storage.total_bytes > 0

    # 12. Delete test files only inside the temporary directory
    mgr.delete_file(file_1)
    mgr.delete_file(file_2)
    mgr.delete_directory(subfolder, recursive=True)

    # 13. Verify cleanup
    final_list = mgr.list_directory(tmp_path)
    assert final_list.total_entries == 0
