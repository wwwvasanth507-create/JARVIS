"""
Unit tests for TaskScheduler start/stop and wake loop.
"""

import time
from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.scheduler.scheduler import TaskScheduler


def test_scheduler_lifecycle():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)
    sched = TaskScheduler(persistence=pers)

    assert sched.is_running is False
    sched.start()
    assert sched.is_running is True
    time.sleep(0.1)
    sched.stop()
    assert sched.is_running is False
