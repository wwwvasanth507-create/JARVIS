"""Unit tests for LongRunningTaskManager, StallDetector, and TaskSupervisorEngine."""

import pytest
from jarvis.core.tasks.task_manager import LongRunningTaskManager, TaskStatus
from jarvis.core.tasks.stall_detector import StallDetector
from jarvis.core.tasks.supervisor import TaskSupervisorEngine


def test_long_running_task_manager_and_lease():
    mgr = LongRunningTaskManager()

    task = mgr.create_task("Long running build task", total_steps=5, idempotency_key="task_key_1")
    assert task.status == TaskStatus.CREATED

    # Acquire worker lease
    acquired = mgr.acquire_lease(task.task_id, worker_id="worker_A", lease_duration_sec=30.0)
    assert acquired is True
    assert task.is_lease_valid() is True

    # Duplicate creation attempt using same idempotency key returns existing task
    task_dup = mgr.create_task("Long running build task", total_steps=5, idempotency_key="task_key_1")
    assert task_dup.task_id == task.task_id


def test_stall_detector_and_supervisor_cycle():
    mgr = LongRunningTaskManager()
    stall_detector = StallDetector(task_manager=mgr, stall_threshold_sec=0.1)
    supervisor = TaskSupervisorEngine(task_manager=mgr, stall_detector=stall_detector)

    task = mgr.create_task("Stalled background task")
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)

    # Force heartbeat progress timestamp into the past
    task.heartbeat.last_progress_time -= 5.0

    report = supervisor.run_supervisor_cycle()
    assert report["stalled_count"] == 1
    assert task.status == TaskStatus.RECOVERING


def test_orphan_task_reconciliation():
    mgr = LongRunningTaskManager()
    supervisor = TaskSupervisorEngine(task_manager=mgr)

    task = mgr.create_task("Orphaned task")
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)

    reconciled = supervisor.reconcile_orphan_tasks_on_startup()
    assert len(reconciled) == 1
    assert task.status == TaskStatus.PAUSED
    assert task.context.get("orphan_reconciled") is True
