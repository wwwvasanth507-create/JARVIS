"""
Unit tests for structured computer and application BaseTool wrappers.
"""

import pytest
from jarvis.tools.computer_tools import (
    MoveMouseTool,
    ClickTool,
    TypeTool,
    ScreenshotTool,
    ActiveWindowTool,
    ListWindowsTool,
)
from jarvis.tools.application_tools import (
    ListApplicationsTool,
    OpenApplicationTool,
    CloseApplicationTool,
    IsApplicationRunningTool,
)


def test_computer_tools_execution():
    move_tool = MoveMouseTool()
    res_move = move_tool.execute(x=200, y=200)
    assert res_move.success is True
    assert move_tool.verify(res_move) is True

    click_tool = ClickTool()
    res_click = click_tool.execute(button="left")
    assert res_click.success is True

    shot_tool = ScreenshotTool()
    res_shot = shot_tool.execute(active_window_only=False)
    assert res_shot.success is True

    act_win_tool = ActiveWindowTool()
    res_act = act_win_tool.execute()
    assert res_act.success is True

    list_win_tool = ListWindowsTool()
    res_list = list_win_tool.execute()
    assert res_list.success is True
    assert len(res_list.data) > 0


def test_application_tools_execution():
    list_app_tool = ListApplicationsTool()
    res_list = list_app_tool.execute()
    assert res_list.success is True
    assert len(res_list.data) > 0

    running_tool = IsApplicationRunningTool()
    res_run = running_tool.execute(name="calc")
    assert res_run.success is True
    assert "is_running" in res_run.data
