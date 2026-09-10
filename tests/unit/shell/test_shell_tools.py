"""
Unit tests for structured shell tools and ToolRegistry integration.
"""

import pytest
from pathlib import Path
from jarvis.shell.manager import ShellManager
from jarvis.tools.shell_tools import (
    ExecuteShellCommandTool,
    GetShellEnvironmentTool,
    GetShellInfoTool,
    ListProcessesTool,
    SHELL_TOOLS,
)


def test_shell_tools_registration():
    assert len(SHELL_TOOLS) == 9
    tool_names = {t.name for t in SHELL_TOOLS}
    assert "shell.execute" in tool_names
    assert "shell.get_environment" in tool_names
    assert "shell.get_shell_info" in tool_names
    assert "shell.list_processes" in tool_names
    assert "shell.terminate_process" in tool_names
    assert "shell.cancel" in tool_names


def test_execute_shell_tool(tmp_path):
    mgr = ShellManager()
    mgr.permission_checker.validator.path_resolver.allowed_roots = [tmp_path.resolve(strict=False)]

    exec_tool = ExecuteShellCommandTool(manager=mgr)
    res = exec_tool.execute(command="python --version", working_directory=str(tmp_path))

    assert res.success
    assert res.data["exit_code"] == 0
    assert "Python" in (res.data["stdout"] + res.data["stderr"])
