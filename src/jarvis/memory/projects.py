"""
Project Memory Manager for JARVIS Memory Subsystem.
"""

from typing import List, Optional
from jarvis.memory.models import ProjectRecord
from jarvis.memory.storage import MemoryStorage


class ProjectManager:
    """Manages project path records and lookup."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def register_project(self, name: str, path: str, description: str = "") -> ProjectRecord:
        existing = self.storage.get_project_by_name(name)
        if existing:
            existing.path = path
            if description:
                existing.description = description
            self.storage.save_project(existing)
            return existing

        project = ProjectRecord(name=name, path=path, description=description)
        self.storage.save_project(project)
        return project

    def get_project(self, name: str) -> Optional[ProjectRecord]:
        return self.storage.get_project_by_name(name)

    def list_projects(self) -> List[ProjectRecord]:
        return self.storage.list_projects()
