"""
Unit tests for Scheduler tools.
"""

from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.manager import SchedulerManager
from jarvis.scheduler.persistence import TaskPersistence
from jarvis.tools.scheduler_tools import (
    SchedulerCreateTool,
    SchedulerListTool,
    SchedulerPauseTool,
    SchedulerResumeTool,
    SchedulerCancelTool,
)


def test_scheduler_tools_workflow():
    db = DatabaseManager(db_path=":memory:")
    pers = TaskPersistence(db_manager=db)
    mgr = SchedulerManager(persistence=pers)

    create_tool = SchedulerCreateTool(manager=mgr)
    list_tool = SchedulerListTool(manager=mgr)
    pause_tool = SchedulerPauseTool(manager=mgr)
    resume_tool = SchedulerResumeTool(manager=mgr)
    cancel_tool = SchedulerCancelTool(manager=mgr)

    # 1. Create
    res = create_tool.execute(name="Test Reminder", schedule_expression="in 10 minutes")
    assert res.success is True
    task_id = res.data["task_id"]

    # 2. List
    list_res = list_tool.execute()
    assert list_res.success is True
    assert len(list_res.data["tasks"]) == 1

    # 3. Pause
    pause_res = pause_tool.execute(task_id=task_id)
    assert pause_res.success is True

    # 4. Resume
    resume_res = resume_tool.execute(task_id=task_id)
    assert resume_res.success is True

    # 5. Cancel
    cancel_res = cancel_tool.execute(task_id=task_id)
    assert cancel_res.success is True
