"""
Integration test suite for SchedulerManager across task scheduling scenarios.
"""

import time
import pytest
from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.manager import SchedulerManager
from jarvis.scheduler.models import TaskState
from jarvis.scheduler.persistence import TaskPersistence


def test_scheduler_end_to_end_reminder():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)
    mgr = SchedulerManager(persistence=pers)

    mgr.start()
    try:
        task = mgr.create_scheduled_task(
            name="Instant Reminder",
            schedule_expression="in 0 seconds",
            action="remind me drink water",
            notification_type="TEXT",
        )
        # Give background thread time to dispatch due task
        time.sleep(0.5)

        runs = mgr.list_history(task_id=task.task_id)
        assert len(runs) >= 1
        assert runs[0].status == TaskState.COMPLETED
    finally:
        mgr.stop()


def test_scheduler_recurring_failure_autopause():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)
    mgr = SchedulerManager(persistence=pers)

    task = mgr.create_scheduled_task(
        name="Failing Scheduled Job",
        schedule_expression="every hour",
        action="invalid_nonexistent_command_12345",
    )

    # Manually simulate 3 failures
    for i in range(3):
        run = mgr.scheduler.worker_pool.executor.execute_scheduled_task(task)
        task.failure_count += 1
        if mgr.policy.check_recurring_failure_limit(task):
            task.status = TaskState.PAUSED

    assert task.status == TaskState.PAUSED
    assert task.failure_count == 3
