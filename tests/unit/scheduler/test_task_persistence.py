"""
Unit tests for TaskPersistence with in-memory SQLite database.
"""

from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState
from jarvis.scheduler.persistence import TaskPersistence


def test_persistence_save_and_get_task():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)

    task = ScheduledTask(name="Test Task", schedule="in 30 mins", action="echo test")
    pers.save_task(task)

    fetched = pers.get_task(task.task_id)
    assert fetched is not None
    assert fetched.name == "Test Task"
    assert fetched.status == TaskState.SCHEDULED


def test_persistence_save_and_list_runs():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)

    task = ScheduledTask(name="Test Task", schedule="in 30 mins")
    pers.save_task(task)

    run = TaskRun(task_id=task.task_id, status=TaskState.COMPLETED, result={"status": "ok"})
    pers.save_run(run)

    runs = pers.list_runs(task_id=task.task_id)
    assert len(runs) == 1
    assert runs[0].status == TaskState.COMPLETED
