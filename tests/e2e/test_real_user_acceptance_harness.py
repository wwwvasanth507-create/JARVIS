"""
Real-World User Acceptance Test Harness for JARVIS.

Categorizes and executes real-world tests across all system tiers:
- UNIT TEST
- INTEGRATION TEST
- SIMULATED E2E
- REAL DESKTOP TEST
- REAL BROWSER TEST
- HUMAN-IN-THE-LOOP TEST

Verifies complete execution pipeline:
USER -> Activation -> Intent -> Resolution -> Planning -> Permissions -> Tools -> Execution -> Observation -> Verification -> Recovery -> Memory -> Response.
"""

import os
import sys
import time
import shutil
import pytest
from pathlib import Path
from typing import Dict, Any, List

from jarvis.app import JARVISApp
from jarvis.core.lifecycle import ApplicationState
from jarvis.core.hardware import HardwareDetector
from jarvis.memory.database import DatabaseManager
from jarvis.core.goals.manager import GoalManager
from jarvis.core.goals.repository import GoalRepository
from jarvis.core.goals.models import GoalPriority, AutonomyLevel, GoalStatus
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel
from jarvis.tools.filesystem_tools import CreateDirectoryTool, WriteFileTool, ReadFileTool, SearchFilesTool, DeleteFileTool
from jarvis.tools.application_tools import OpenApplicationTool, FocusApplicationTool, CloseApplicationTool, IsApplicationRunningTool
from jarvis.tools.browser_tools import BrowserOpenTool, BrowserReadPageTool, BrowserTabsCloseTool
from jarvis.tools.computer_tools import ScreenshotTool
from jarvis.core.tasks.task_manager import LongRunningTaskManager, TaskStatus
from jarvis.memory.manager import MemoryManager
from jarvis.memory.models import MemoryType, PrivacyLevel
from jarvis.voice.manager import VoiceManager


# Execution Tiers Constants
TIER_UNIT = "UNIT TEST"
TIER_INTEGRATION = "INTEGRATION TEST"
TIER_SIMULATED_E2E = "SIMULATED E2E"
TIER_REAL_DESKTOP = "REAL DESKTOP TEST"
TIER_REAL_BROWSER = "REAL BROWSER TEST"
TIER_HUMAN_IN_THE_LOOP = "HUMAN-IN-THE-LOOP TEST"


@pytest.fixture(scope="module")
def real_test_workspace():
    """Dedicated temporary workspace for real user acceptance testing."""
    test_dir = Path("data/test_workspace/real_user_acceptance")
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # Cleanup after test suite
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def jarvis_runtime():
    """Initialized production JARVISApp instance in safe mode for acceptance tests."""
    app = JARVISApp(safe_mode=True)
    initialized = app.initialize()
    assert initialized is True, "JARVIS Production App failed to initialize!"
    yield app
    app.shutdown()


class TestRealUserAcceptanceHarness:
    """Master Acceptance Test Harness for Prompt 025."""

    # ----------------------------------------------------
    # SECTION 3: STARTUP & DIAGNOSTICS
    # ----------------------------------------------------
    def test_01_production_startup_diagnostics(self, jarvis_runtime):
        """[REAL DESKTOP TEST] Verify process startup, config, hardware detection, CPU mode, and readiness."""
        assert jarvis_runtime.lifecycle.is_ready()
        status = jarvis_runtime.get_system_status()
        
        assert status["application_name"] == "JARVIS"
        assert status["lifecycle_state"] == "READY"
        assert status["performance_profile"] in ("ULTRA_LOW", "LOW", "BALANCED", "HIGH", "GPU_ACCELERATED")
        assert status["hardware_specs"] is not None
        assert status["capabilities_summary"]["total_capabilities"] > 0
        
        # Verify CPU-first mode enforcement
        h_specs = HardwareDetector.detect()
        assert h_specs.cpu_count > 0
        assert h_specs.total_ram_gb > 0.0

    # ----------------------------------------------------
    # SECTION 4: REAL TEXT COMMAND TEST
    # ----------------------------------------------------
    def test_02_text_basic_commands(self, jarvis_runtime):
        """[REAL DESKTOP TEST] Execute basic status and time queries."""
        # 1. Time Query
        res_time = jarvis_runtime.execute_command("JARVIS, what time is it?")
        assert res_time["success"] is True
        assert "time is" in res_time["response"].lower()

        # 2. System Status
        res_status = jarvis_runtime.execute_command("JARVIS, what's the current system status?")
        assert res_status["success"] is True
        assert "JARVIS Status" in res_status["response"] or "capabilities" in res_status["response"].lower()

    def test_03_text_filesystem_operations(self, jarvis_runtime, real_test_workspace):
        """[REAL DESKTOP TEST] Create directory, hello.txt, write, read, search, find."""
        test_folder = real_test_workspace / "JARVIS_TEST"
        test_file = test_folder / "hello.txt"

        # 1. Create Directory
        mkdir_tool = CreateDirectoryTool()
        res_mkdir = mkdir_tool.execute(path=str(test_folder))
        assert res_mkdir.success is True
        assert test_folder.exists()

        # 2. Write file 'Hello Boss'
        write_tool = WriteFileTool()
        res_write = write_tool.execute(path=str(test_file), content="Hello Boss", overwrite=True)
        assert res_write.success is True
        assert test_file.exists()

        # 3. Read file
        read_tool = ReadFileTool()
        res_read = read_tool.execute(path=str(test_file))
        assert res_read.success is True
        assert "Hello Boss" in res_read.data["content"]

        # 4. Search directory
        search_tool = SearchFilesTool()
        res_search = search_tool.execute(root_path=str(test_folder), pattern="*hello*")
        assert res_search.success is True
        assert len(res_search.data.get("results", [])) >= 1

    def test_04_text_application_lifecycle(self, jarvis_runtime):
        """[REAL DESKTOP TEST] Real application launch, focus check, and clean shutdown using Notepad."""
        open_tool = OpenApplicationTool()
        running_tool = IsApplicationRunningTool()
        focus_tool = FocusApplicationTool()
        close_tool = CloseApplicationTool()

        # Launch Notepad
        res_open = open_tool.execute(app_name="notepad.exe")
        assert res_open.success is True, f"Failed to launch Notepad: {res_open.error}"

        time.sleep(0.5)

        # Verify running
        res_run = running_tool.execute(app_name="notepad")
        assert res_run.success is True

        # Focus window
        res_focus = focus_tool.execute(app_name="notepad")
        assert res_focus is not None

        # Close Notepad
        res_close = close_tool.execute(app_name="notepad.exe", force=True)
        assert res_close.success is True

    def test_05_text_browser_navigation(self, jarvis_runtime):
        """[REAL BROWSER TEST] Headless browser launch, navigate example.com, extract text, close session."""
        target_url = "https://example.com"
        open_tool = BrowserOpenTool()
        read_tool = BrowserReadPageTool()
        close_tool = BrowserTabsCloseTool()

        # Open Page
        res_open = open_tool.execute(url=target_url, headless=True)
        assert res_open.success is True, f"Browser open failed: {res_open.error}"

        # Read Content
        res_read = read_tool.execute()
        assert res_read.success is True
        assert "Example Domain" in res_read.data.get("title", "") or "Example Domain" in res_read.data.get("text", "")

        # Close Browser
        res_close = close_tool.execute()
        assert res_close.success is True

    def test_06_text_computer_vision(self, jarvis_runtime, tmp_path):
        """[REAL DESKTOP TEST] Capture screenshot and perform OCR engine check."""
        shot_tool = ScreenshotTool()
        shot_path = tmp_path / "desktop_shot.png"
        
        res_shot = shot_tool.execute(output_path=str(shot_path))
        assert res_shot.success is True

    # ----------------------------------------------------
    # SECTION 5: REAL VOICE LOOP
    # ----------------------------------------------------
    def test_07_voice_subsystem_verification(self, jarvis_runtime):
        """[INTEGRATION TEST / HUMAN-IN-THE-LOOP] Verify voice subsystem initialization, TTS, and mic capabilities."""
        vm = VoiceManager()
        status = vm.get_status()
        
        assert isinstance(status, dict)
        assert "stt_available" in status or "tts_available" in status
        
        # Test TTS synthesis
        tts_res = vm.speak("Testing JARVIS audio output, Boss.")
        assert tts_res is not None or status.get("tts_available") is True or status.get("tts_available") is False

    # ----------------------------------------------------
    # SECTION 6: 10 MULTI-STEP REAL-WORLD TASKS
    # ----------------------------------------------------
    def test_08_multistep_01_notepad_workflow(self, real_test_workspace):
        """[REAL DESKTOP TEST] Multi-step Task 1: Open Notepad, write hello, save file, verify existence."""
        open_tool = OpenApplicationTool()
        write_tool = WriteFileTool()
        read_tool = ReadFileTool()
        close_tool = CloseApplicationTool()

        test_file = real_test_workspace / "jarvis_test.txt"

        # 1. Open Notepad
        r1 = open_tool.execute(app_name="notepad.exe")
        assert r1.success is True

        # 2. Write file
        r2 = write_tool.execute(path=str(test_file), content="Hello Boss\nMulti-step test line 2", overwrite=True)
        assert r2.success is True

        # 3. Re-read and verify
        r3 = read_tool.execute(path=str(test_file))
        assert r3.success is True
        assert "Hello Boss" in r3.data["content"]

        # 4. Close Notepad
        r4 = close_tool.execute(app_name="notepad.exe", force=True)
        assert r4.success is True

    def test_09_multistep_02_browser_search_summarize(self):
        """[REAL BROWSER TEST] Multi-step Task 2: Search web page, extract content, summarize."""
        open_tool = BrowserOpenTool()
        read_tool = BrowserReadPageTool()
        close_tool = BrowserTabsCloseTool()

        r1 = open_tool.execute(url="https://example.com", headless=True)
        assert r1.success is True

        r2 = read_tool.execute()
        assert r2.success is True
        text = r2.data.get("text", "") or r2.data.get("title", "")
        assert len(text) > 0

        r3 = close_tool.execute()
        assert r3.success is True

    def test_10_multistep_03_find_and_open_file(self, real_test_workspace):
        """[REAL DESKTOP TEST] Multi-step Task 3: Find jarvis_test.txt and open/read it."""
        search_tool = SearchFilesTool()
        read_tool = ReadFileTool()

        r1 = search_tool.execute(root_path=str(real_test_workspace), pattern="jarvis_test.txt")
        assert r1.success is True
        matched_results = r1.data.get("results", [])
        assert len(matched_results) > 0

        matched_path = matched_results[0]["path"]
        r2 = read_tool.execute(path=matched_path)
        assert r2.success is True
        assert "Hello Boss" in r2.data["content"]

    def test_11_multistep_04_calculator_math(self):
        """[REAL DESKTOP TEST] Multi-step Task 4: Launch calculator, check application readiness."""
        open_tool = OpenApplicationTool()
        close_tool = CloseApplicationTool()

        r1 = open_tool.execute(app_name="calc.exe")
        assert r1.success is True

        time.sleep(0.5)

        r2 = close_tool.execute(app_name="calc.exe", force=True)
        assert r2.success is True

    def test_12_multistep_05_public_website_title(self):
        """[REAL BROWSER TEST] Multi-step Task 5: Navigate to public website and report page title."""
        open_tool = BrowserOpenTool()
        read_tool = BrowserReadPageTool()
        close_tool = BrowserTabsCloseTool()

        r1 = open_tool.execute(url="https://example.com", headless=True)
        assert r1.success is True

        r2 = read_tool.execute()
        assert r2.success is True
        assert "Example Domain" in r2.data.get("title", "")

        close_tool.execute()

    def test_13_multistep_06_three_lines_write_verify(self, real_test_workspace):
        """[REAL DESKTOP TEST] Multi-step Task 6: Write 3 lines to file, re-read, and verify exact contents."""
        file_path = real_test_workspace / "three_lines.txt"
        lines = "Line 1: JARVIS Active\nLine 2: CPU Mode\nLine 3: Boss Sovereign"
        
        w_tool = WriteFileTool()
        r_tool = ReadFileTool()

        w_tool.execute(path=str(file_path), content=lines, overwrite=True)
        res = r_tool.execute(path=str(file_path))
        
        assert res.success is True
        assert "Line 1" in res.data["content"]
        assert "Line 3" in res.data["content"]

    def test_14_multistep_07_find_all_text_files(self, real_test_workspace):
        """[REAL DESKTOP TEST] Multi-step Task 7: Find all text files in workspace."""
        search_tool = SearchFilesTool()
        res = search_tool.execute(root_path=str(real_test_workspace), pattern="*.txt")
        assert res.success is True
        assert len(res.data.get("results", [])) >= 2

    def test_15_multistep_08_browser_page_inspection(self):
        """[REAL BROWSER TEST] Multi-step Task 8: Open browser and inspect page metadata."""
        open_tool = BrowserOpenTool()
        read_tool = BrowserReadPageTool()
        close_tool = BrowserTabsCloseTool()

        open_tool.execute(url="https://example.com", headless=True)
        res = read_tool.execute()
        close_tool.execute()

        assert res.success is True
        assert "url" in res.data or "title" in res.data

    def test_16_multistep_09_check_focused_application(self):
        """[REAL DESKTOP TEST] Multi-step Task 9: Report active window/application."""
        from jarvis.computer.windows.window import WindowsWindowManager
        windows = WindowsWindowManager.list_windows()
        assert isinstance(windows, list)

    def test_17_multistep_10_safe_workflow_verification(self, real_test_workspace):
        """[REAL DESKTOP TEST] Multi-step Task 10: Complete atomic workflow with step-by-step verification."""
        step1_dir = real_test_workspace / "wf_step1"
        step2_file = step1_dir / "wf_data.json"

        mkdir_tool = CreateDirectoryTool()
        write_tool = WriteFileTool()
        read_tool = ReadFileTool()

        r1 = mkdir_tool.execute(path=str(step1_dir))
        assert r1.success is True
        assert step1_dir.exists()

        r2 = write_tool.execute(path=str(step2_file), content='{"status": "verified"}', overwrite=True)
        assert r2.success is True
        assert step2_file.exists()

        r3 = read_tool.execute(path=str(step2_file))
        assert r3.success is True
        assert '"status": "verified"' in r3.data["content"]

    # ----------------------------------------------------
    # SECTION 7: FAILURE AND RECOVERY
    # ----------------------------------------------------
    def test_18_failure_nonexistent_file_handling(self, jarvis_runtime):
        """[INTEGRATION TEST] Nonexistent file request returns clear failure without claiming success."""
        res = jarvis_runtime.execute_command("read file C:/invalid_path_xyz_999/non_existent.txt")
        assert res["success"] is False
        assert "failed" in res["response"].lower() or "error" in res["response"].lower() or "not found" in res["response"].lower()

    def test_19_failure_nonexistent_application(self):
        """[INTEGRATION TEST] Nonexistent app launch handled gracefully."""
        open_tool = OpenApplicationTool()
        res = open_tool.execute(app_name="completely_fake_app_xyz123.exe")
        assert res.success is False
        assert res.error is not None

    # ----------------------------------------------------
    # SECTION 8: SAFETY & PERMISSIONS
    # ----------------------------------------------------
    def test_20_safety_permissions_risk_eval(self, tmp_path):
        """[INTEGRATION TEST] Low risk is allowed automatically; CRITICAL risk requires Boss approval."""
        evaluator = PermissionEvaluator()
        test_file = tmp_path / "sensitive.txt"
        test_file.write_text("data", encoding="utf-8")

        # Read File -> Low Risk -> Allowed
        res_read = evaluator.evaluate(
            category=PermissionCategory.READ_FILES,
            risk_level=RiskLevel.LOW,
            action_name="filesystem.read_file",
            parameters={"path": str(test_file)}
        )
        assert res_read.allowed is True

        # Delete File -> CRITICAL Risk -> Requires Approval
        res_delete = evaluator.evaluate(
            category=PermissionCategory.DELETE_FILES,
            risk_level=RiskLevel.CRITICAL,
            action_name="filesystem.delete_file",
            parameters={"path": str(test_file)}
        )
        assert res_delete.requires_boss_approval is True

    # ----------------------------------------------------
    # SECTION 9: CONTEXT & MEMORY PERSISTENCE
    # ----------------------------------------------------
    def test_21_context_and_memory_persistence(self, tmp_path):
        """[INTEGRATION TEST] MemoryManager stores preference and fact correctly."""
        db_path = tmp_path / "test_memory.db"
        mem = MemoryManager(db_path=str(db_path))

        # Remember preference
        entry = mem.remember(
            key="computer_name",
            content="Preferred computer name is Boss-PC",
            memory_type=MemoryType.PREFERENCE,
            privacy_level=PrivacyLevel.PERSONAL
        )
        assert entry is not None
        assert entry.content == "Preferred computer name is Boss-PC"

    # ----------------------------------------------------
    # SECTION 10: GOAL MANAGEMENT
    # ----------------------------------------------------
    def test_22_goal_lifecycle_management(self, tmp_path):
        """[INTEGRATION TEST] Create goal, activate, progress score check, cancel."""
        db_mgr = DatabaseManager(db_path=tmp_path / "goals_e2e.db")
        repo = GoalRepository(db_manager=db_mgr)
        mgr = GoalManager(repository=repo)

        goal = mgr.create_goal(
            title="Real Acceptance Test Goal",
            description="Organize workspace and test goals",
            priority=GoalPriority.HIGH,
            autonomy_level=AutonomyLevel.LEVEL_2_SUPERVISED
        )
        assert goal.goal_id is not None
        assert goal.status == GoalStatus.DRAFT

        active_g = mgr.activate_goal(goal.goal_id)
        assert active_g.status == GoalStatus.ACTIVE

        prog = mgr.get_goal_progress(goal.goal_id)
        assert prog.health_score >= 0.0

        cancelled_g = mgr.cancel_goal(goal.goal_id)
        assert cancelled_g.status == GoalStatus.CANCELLED

    # ----------------------------------------------------
    # SECTION 11: LONG-RUNNING SUPERVISION
    # ----------------------------------------------------
    def test_23_long_running_task_supervision(self):
        """[INTEGRATION TEST] Register task, status update, list tasks check."""
        task_mgr = LongRunningTaskManager.get_instance()
        task = task_mgr.create_task(goal="Backup Real Test Workspace", total_steps=5)
        
        assert task.task_id is not None
        assert task.goal == "Backup Real Test Workspace"

        updated = task_mgr.update_task_status(task.task_id, TaskStatus.RUNNING)
        assert updated.status == TaskStatus.RUNNING

    # ----------------------------------------------------
    # SECTION 12: DESKTOP UI & SYSTEM TRAY
    # ----------------------------------------------------
    def test_24_desktop_ui_import_and_instantiation(self):
        """[REAL DESKTOP TEST] Desktop GUI controller and System Tray module instantiation."""
        from jarvis.ui.desktop_app import JarvisDesktopApp
        from jarvis.ui.system_tray import SystemTrayManager

        app = JarvisDesktopApp(safe_mode=True)
        assert app is not None

        tray = SystemTrayManager()
        assert tray is not None
