"""
Task Memory Manager for JARVIS Memory Subsystem.
"""

from typing import List, Optional
from jarvis.memory.models import TaskRecord, TaskStatus
from jarvis.memory.storage import MemoryStorage


class TaskManager:
    """Manages lightweight user tasks."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def create_task(self, title: str, description: str = "", priority: int = 1) -> TaskRecord:
        task = TaskRecord(title=title, description=description, priority=priority)
        self.storage.save_task(task)
        return task

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> Optional[TaskRecord]:
        tasks = self.storage.list_tasks()
        for task in tasks:
            if task.task_id == task_id:
                task.status = new_status
                self.storage.save_task(task)
                return task
        return None

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskRecord]:
        return self.storage.list_tasks(status=status)
