"""
End-to-End Production Integration Tests for JARVIS Desktop Assistant.

Validates:
- Real end-to-end safe task pipelines (Scenarios A through H)
- Strict false-success rejection
- Command cancellation
- Scheduler persistence across restarts
"""

import pytest
from pathlib import Path
from jarvis.app import JARVISApp
from jarvis.core.orchestration.orchestrator import JarvisOrchestrator, ExecutionStatus


@pytest.fixture
def running_app():
    app = JARVISApp(safe_mode=True)
    assert app.initialize()
    yield app
    app.shutdown()


def test_scenario_fast_path_time(running_app):
    res = running_app.execute_command("what time is it")
    assert res["success"] is True
    assert res["verified"] is True
    assert "current time" in res["response"].lower()


def test_scenario_read_file(running_app, tmp_path):
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("Hello Boss, JARVIS is operational.", encoding="utf-8")

    res = running_app.execute_command(f"read this file {test_file}")
    assert res["success"] is True
    assert res["verified"] is True


def test_false_success_rejection():
    """Verify that unsuccessful operations do NOT report false-success."""
    orchestrator = JarvisOrchestrator()
    # Processing an invalid/non-existent command should fail cleanly
    state = orchestrator.handle("invalid_action_nonexistent_xyz")
    assert state.status in [ExecutionStatus.FAILED, ExecutionStatus.NEEDS_CLARIFICATION]


def test_command_cancellation(running_app):
    res = running_app.execute_command("cancel current operation")
    assert res["success"] is True or "cancel" in res["response"].lower()


def test_scheduler_restart_persistence(tmp_path):
    from jarvis.memory.database import DatabaseManager
    from jarvis.scheduler.manager import SchedulerManager
    from jarvis.scheduler.persistence import TaskPersistence
    
    db_file = tmp_path / "test_sched.db"
    db_mgr = DatabaseManager(db_path=db_file)
    persistence = TaskPersistence(db_manager=db_mgr)
    
    # 1. Create and schedule a task
    sched1 = SchedulerManager(persistence=persistence)
    sched1.start()
    task = sched1.create_scheduled_task(
        name="Submit Report Reminder",
        schedule_expression="in 2 hours",
        action="Remind me to submit report"
    )
    task_id = task.task_id
    sched1.stop()

    # 2. Restart scheduler instance using same database
    sched2 = SchedulerManager(persistence=persistence)
    sched2.start()
    persisted_task = sched2.get_task(task_id)
    assert persisted_task is not None
    assert persisted_task.name == "Submit Report Reminder"
    sched2.stop()
    db_mgr.close()

