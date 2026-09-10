"""
Unit tests for 6 screen tools.
"""

import pytest
from jarvis.tools.screen_tools import (
    ScreenCaptureTool,
    ScreenReadTextTool,
    ScreenAnalyzeTool,
    ScreenDescribeTool,
    ScreenFindTool,
    ScreenCompareTool,
    SCREEN_TOOLS
)
from jarvis.security.permissions import PermissionCategory, RiskLevel


def test_screen_tools_count():
    assert len(SCREEN_TOOLS) == 6


def test_screen_capture_tool():
    tool = ScreenCaptureTool()
    assert tool.metadata.name == "screen.capture"
    assert tool.metadata.permission_requirement == PermissionCategory.SCREEN_READ
    assert tool.metadata.risk_level == RiskLevel.LOW

    res = tool.execute(mode="FULL_SCREEN")
    assert res.success is True
    assert res.data["width"] > 0


def test_screen_describe_tool():
    tool = ScreenDescribeTool()
    res = tool.execute()
    assert res.success is True
    assert "description" in res.data
