"""
Unit tests for structured filesystem tools and ToolRegistry integration.
"""

import pytest
from pathlib import Path
from jarvis.filesystem.manager import FilesystemManager
from jarvis.tools.filesystem_tools import (
    ListDirectoryTool,
    ReadFileTool,
    CreateFileTool,
    WriteFileTool,
    EditFileTool,
    CopyFileTool,
    MoveFileTool,
    DeleteFileTool,
    FILESYSTEM_TOOLS,
)


def test_filesystem_tools_registration():
    assert len(FILESYSTEM_TOOLS) == 16
    tool_names = {t.name for t in FILESYSTEM_TOOLS}
    assert "filesystem.list_directory" in tool_names
    assert "filesystem.read_file" in tool_names
    assert "filesystem.create_file" in tool_names
    assert "filesystem.write_file" in tool_names
    assert "filesystem.edit_file" in tool_names
    assert "filesystem.delete_file" in tool_names
    assert "filesystem.search" in tool_names
    assert "filesystem.find_duplicates" in tool_names


def test_create_read_write_tool_execution(tmp_path, monkeypatch):
    # Initialize manager configured with tmp_path as allowed root
    mgr = FilesystemManager()
    mgr.permission_checker.path_resolver.allowed_roots = [tmp_path.resolve(strict=False)]

    create_tool = CreateFileTool(manager=mgr)
    read_tool = ReadFileTool(manager=mgr)
    write_tool = WriteFileTool(manager=mgr)

    target_path = str(tmp_path / "tool_test.txt")

    # 1. Create file tool
    c_res = create_tool.execute(path=target_path, content="Tool creation test", overwrite=True)
    assert c_res.success
    assert c_res.data["path"] == str(Path(target_path).resolve(strict=False))

    # 2. Read file tool
    r_res = read_tool.execute(path=target_path)
    assert r_res.success
    assert r_res.data["content"] == "Tool creation test"

    # 3. Write file tool
    w_res = write_tool.execute(path=target_path, content="Updated via tool", overwrite=True)
    assert w_res.success

    r_res2 = read_tool.execute(path=target_path)
    assert r_res2.data["content"] == "Updated via tool"
