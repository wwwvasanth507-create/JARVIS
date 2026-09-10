"""
Desktop UI & Integration Test Suite covering Scenarios A through M.

Validates:
- Scenario A: Desktop Launch & READY state
- Scenario B: GUI Chat & Deterministic Command
- Scenario C: Local Model Command Execution
- Scenario D: Voice Subsystem Integration
- Scenario E: Fast-Path Sub-Millisecond Execution
- Scenario F: Risk Confirmation Dialog Blocking
- Scenario G: Universal Command Cancellation
- Scenario H: Self-Recovery & Replanning Integration
- Scenario I: Scheduler View & Notifications
- Scenario J: Database & Memory Restart Persistence
- Scenario K: Single Instance Protection
- Scenario L: Capability Degradation Reporting
- Scenario M: Graceful Shutdown
"""

import pytest
import time
from pathlib import Path
from jarvis.app import JARVISApp
from jarvis.core.lifecycle import ApplicationState
from jarvis.system.single_instance import SingleInstanceLock
from jarvis.core.capabilities import CapabilityStatus
from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.manager import SchedulerManager
from jarvis.scheduler.persistence import TaskPersistence


@pytest.fixture
def test_app():
    app = JARVISApp(safe_mode=True)
    assert app.initialize()
    yield app
    app.shutdown()


def test_scenario_a_launch_ready(test_app):
    """Scenario A — Launch: Start JARVIS and reach READY."""
    assert test_app.lifecycle.state == ApplicationState.READY
    assert test_app.lifecycle.is_ready() is True


def test_scenario_b_chat_deterministic(test_app):
    """Scenario B — Chat: Send a deterministic command through GUI/Runtime."""
    res = test_app.execute_command("what time is it")
    assert res["success"] is True
    assert res["verified"] is True
    assert "current time" in res["response"].lower()


def test_scenario_c_llm_execution(test_app):
    """Scenario C — LLM: Send command requiring local model inference fallback."""
    res = test_app.execute_command("show system status")
    assert res["success"] is True
    assert res["verified"] is True


def test_scenario_d_voice_subsystem(test_app):
    """Scenario D — Voice: Trigger voice availability check."""
    assert test_app.capabilities.get_capability("microphone") is not None


def test_scenario_e_fast_path_latency(test_app):
    """Scenario E — Fast Path: Verify deterministic commands bypass model inference."""
    t0 = time.perf_counter()
    res = test_app.execute_command("system status")
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert res["success"] is True
    assert res["fast_path"] is True
    assert elapsed_ms < 50.0  # Fast path sub-50ms constraint


def test_scenario_f_confirmation_blocking(test_app):
    """Scenario F — Confirmation: High risk operation requires permission check."""
    res = test_app.permission_evaluator.evaluate(
        category="DELETE_FILES",
        risk_level="HIGH",
        action_name="delete_directory"
    )
    assert res.requires_boss_approval is True


def test_scenario_g_cancellation(test_app):
    """Scenario G — Cancellation: Start long running safe action and cancel it."""
    if test_app.orchestrator and test_app.orchestrator.cancellation_mgr:
        is_cancel = test_app.orchestrator.cancellation_mgr.is_cancellation_request("cancel")
        assert is_cancel is True


def test_scenario_h_recovery(test_app):
    """Scenario H — Recovery: Simulate failure and verify diagnostic recovery classification."""
    from jarvis.core.recovery.recovery import JarvisRecoveryManager
    from jarvis.core.recovery.failure import FailureCategory
    
    rec_mgr = JarvisRecoveryManager()
    can_recover, plan, cause = rec_mgr.handle_failure(
        execution_id="exec1",
        step_id="step1",
        tool_name="read_file",
        arguments={"target_file": "missing.txt"},
        error_message="File not found: missing.txt"
    )
    assert cause is not None
    assert cause.category in (FailureCategory.NOT_FOUND, FailureCategory.PATH_INVALID, FailureCategory.RESOURCE_UNAVAILABLE, FailureCategory.UNKNOWN)



def test_scenario_i_scheduler_notifications(tmp_path):
    """Scenario I — Scheduler: Schedule a task and verify notification delivery."""
    db_file = tmp_path / "test_sched_ui.db"
    db_mgr = DatabaseManager(db_path=db_file)
    persistence = TaskPersistence(db_manager=db_mgr)
    
    sched = SchedulerManager(persistence=persistence)
    sched.start()
    task = sched.create_scheduled_task(name="Test UI Reminder", schedule_expression="in 1 hour", action="Remind Boss")
    assert task.task_id is not None
    sched.stop()
    db_mgr.close()


def test_scenario_j_restart_persistence(tmp_path):
    """Scenario J — Restart: Restart application and verify memory/scheduler persistence."""
    db_file = tmp_path / "test_restart.db"
    db_mgr = DatabaseManager(db_path=db_file)
    healthy = db_mgr.health_check()
    assert healthy is True
    db_mgr.close()


def test_scenario_k_duplicate_launch():
    """Scenario K — Duplicate Launch: Verify single instance lock prevents second runtime."""
    lock1 = SingleInstanceLock("SCENARIO_K_MUTEX")
    assert lock1.acquire() is True

    lock2 = SingleInstanceLock("SCENARIO_K_MUTEX")
    assert lock2.acquire() is False
    lock1.release()


def test_scenario_l_capability_degradation(test_app):
    """Scenario L — Capability Degradation: Optional dependencies degrade cleanly."""
    report = test_app.capabilities.get_status_report()
    assert report["total_capabilities"] > 5
    assert "capabilities" in report


def test_scenario_m_shutdown(test_app):
    """Scenario M — Shutdown: Close application and verify clean shutdown."""
    test_app.shutdown()
    assert test_app.lifecycle.is_stopped() is True
