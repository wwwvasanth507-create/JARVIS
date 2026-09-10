"""
Unit tests for application tools and ToolRegistry integration.
"""

import pytest
from jarvis.tools.application_tools import (
    ListApplicationsTool,
    FindApplicationTool,
    IsApplicationRunningTool,
    CheckApplicationHealthTool,
    APPLICATION_TOOLS,
)


def test_application_tools_registration():
    assert len(APPLICATION_TOOLS) == 12
    tool_names = {t.name for t in APPLICATION_TOOLS}
    assert "application.list" in tool_names
    assert "application.find" in tool_names
    assert "application.open" in tool_names
    assert "application.close" in tool_names
    assert "application.restart" in tool_names
    assert "application.is_running" in tool_names
    assert "application.list_running" in tool_names
    assert "application.focus" in tool_names
    assert "application.health" in tool_names
    assert "application.open_file" in tool_names
    assert "application.open_url" in tool_names
    assert "application.list_startup" in tool_names


def test_list_and_find_tools_execution():
    list_tool = ListApplicationsTool()
    res_list = list_tool.execute()
    assert res_list.success
    assert len(res_list.data) > 0

    find_tool = FindApplicationTool()
    res_find = find_tool.execute(query="calculator")
    assert res_find.success
    assert res_find.data["name"] == "Calculator"
