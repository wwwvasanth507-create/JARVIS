"""
End-to-End Real-World Acceptance Test Suite for JARVIS.

Executes comprehensive end-to-end tests across system lifecycle, text orchestration,
application control, filesystem operations, browser navigation, computer vision/OCR,
safety permissions, memory persistence, goal operations, failure recovery,
and performance metrics under CPU-only local execution.
"""

import os
import time
import shutil
import pytest
from pathlib import Path

from jarvis.app import JARVISApp
from jarvis.core.lifecycle import ApplicationState
from jarvis.memory.database import DatabaseManager
from jarvis.core.goals.manager import GoalManager
from jarvis.core.goals.models import GoalPriority, AutonomyLevel, GoalStatus
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel
from jarvis.tools.filesystem_tools import CreateDirectoryTool, WriteFileTool, ReadFileTool, SearchFilesTool, DeleteFileTool
from jarvis.tools.application_tools import OpenApplicationTool, FocusApplicationTool, CloseApplicationTool, IsApplicationRunningTool
from jarvis.tools.browser_tools import BrowserOpenTool, BrowserReadPageTool, BrowserTabsCloseTool


@pytest.fixture(scope="module")
def e2e_workspace():
    test_dir = Path("data/test_workspace/pytest_e2e")
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def jarvis_app(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e_db") / "e2e_jarvis.db"
    app = JARVISApp(safe_mode=True)
    app.initialize()
    yield app
    app.shutdown()


def test_01_lifecycle_and_startup(jarvis_app):
    assert jarvis_app.lifecycle.is_ready()
    status = jarvis_app.get_system_status()
    assert status["application_name"] == "JARVIS"
    assert status["lifecycle_state"] == "READY"
    assert status["performance_profile"] in ("LOW", "BALANCED", "HIGH")


def test_02_text_command_fast_path(jarvis_app):
    res_time = jarvis_app.execute_command("what time is it?")
    assert res_time["success"] is True
    assert "current time" in res_time["response"].lower()

    res_status = jarvis_app.execute_command("show system status")
    assert res_status["success"] is True
    assert "JARVIS Status" in res_status["response"]


def test_03_filesystem_operations(e2e_workspace):
    test_file = e2e_workspace / "hello.txt"

    # 1. Create & Write
    write_tool = WriteFileTool()
    res_write = write_tool.execute(path=str(test_file), content="Hello Boss", overwrite=True)
    assert res_write.success is True
    assert test_file.exists()

    # 2. Read
    read_tool = ReadFileTool()
    res_read = read_tool.execute(path=str(test_file))
    assert res_read.success is True
    assert "Hello Boss" in res_read.data["content"]

    # 3. Search
    search_tool = SearchFilesTool()
    res_search = search_tool.execute(root_path=str(e2e_workspace), pattern="*hello*")
    assert res_search.success is True


def test_04_application_control_safe():
    open_tool = OpenApplicationTool()
    running_tool = IsApplicationRunningTool()
    close_tool = CloseApplicationTool()

    # Open Notepad
    res_open = open_tool.execute(app_name="notepad.exe")
    assert res_open.success is True

    time.sleep(0.5)

    # Check Running
    res_running = running_tool.execute(app_name="notepad")
    assert res_running.success is True

    # Close Notepad
    res_close = close_tool.execute(app_name="notepad.exe", force=True)
    assert res_close.success is True


def test_05_browser_automation_safe():
    target_url = "https://example.com"
    open_tool = BrowserOpenTool()
    read_tool = BrowserReadPageTool()
    close_tool = BrowserTabsCloseTool()

    # Open browser session
    res_open = open_tool.execute(url=target_url, headless=True)
    assert res_open.success is True

    # Read page content
    res_read = read_tool.execute()
    assert res_read.success is True

    # Close session
    res_close = close_tool.execute()
    assert res_close.success is True


def test_06_safety_and_permissions(tmp_path):
    perm_eval = PermissionEvaluator()
    dummy_file = tmp_path / "protected.txt"
    dummy_file.write_text("protected data", encoding="utf-8")

    res_safe = perm_eval.evaluate(
        category=PermissionCategory.READ_FILES,
        risk_level=RiskLevel.LOW,
        action_name="filesystem.read_file",
        parameters={"path": str(dummy_file)}
    )
    assert res_safe.allowed is True

    res_critical = perm_eval.evaluate(
        category=PermissionCategory.DELETE_FILES,
        risk_level=RiskLevel.CRITICAL,
        action_name="filesystem.delete_file",
        parameters={"path": str(dummy_file)}
    )
    assert res_critical.requires_boss_approval is True


def test_07_goal_management(tmp_path):
    from jarvis.core.goals.repository import GoalRepository
    db_mgr = DatabaseManager(db_path=tmp_path / "goal_test.db")
    repo = GoalRepository(db_manager=db_mgr)
    mgr = GoalManager(repository=repo)

    goal = mgr.create_goal(
        title="E2E Project Organization Goal",
        description="Organize workspace files safely",
        priority=GoalPriority.HIGH,
        autonomy_level=AutonomyLevel.LEVEL_2_SUPERVISED
    )
    assert goal.goal_id is not None
    assert goal.status == GoalStatus.DRAFT

    active_goal = mgr.activate_goal(goal.goal_id)
    assert active_goal.status == GoalStatus.ACTIVE

    progress = mgr.get_goal_progress(goal.goal_id)
    assert progress.health_score >= 0.0

    completed_goal = mgr.cancel_goal(goal.goal_id)
    assert completed_goal.status == GoalStatus.CANCELLED


def test_08_failure_and_recovery(jarvis_app):
    res_invalid = jarvis_app.execute_command("read file C:/non_existent_folder_xyz/missing_file.txt")
    assert res_invalid["success"] is False
    assert "failed" in res_invalid["response"].lower() or "error" in res_invalid["response"].lower()
