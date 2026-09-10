"""
SQL Storage Repository for JARVIS Memory Subsystem.
"""

import json
import time
from typing import Any, Dict, List, Optional
from jarvis.memory.database import DatabaseManager
from jarvis.memory.models import (
    ConversationSummary,
    Episode,
    KnowledgeDocument,
    MemoryItem,
    MemoryType,
    PrivacyLevel,
    MemoryConfidence,
    ProjectRecord,
    TaskRecord,
    TaskStatus,
)


class MemoryStorage:
    """Provides SQL persistent CRUD operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_mgr = db_manager

    # --- MemoryItem CRUD ---

    def save_memory(self, item: MemoryItem) -> None:
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memories (
                    id, type, key, content, metadata_json, source, confidence,
                    importance, created_at, updated_at, last_accessed_at, expires_at,
                    privacy_level, access_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.type.value if hasattr(item.type, "value") else str(item.type),
                    item.key,
                    item.content,
                    json.dumps(item.metadata),
                    item.source,
                    item.confidence.value if hasattr(item.confidence, "value") else str(item.confidence),
                    item.importance,
                    item.created_at,
                    item.updated_at,
                    item.last_accessed_at,
                    item.expires_at,
                    item.privacy_level.value if hasattr(item.privacy_level, "value") else str(item.privacy_level),
                    item.access_count,
                ),
            )
            conn.commit()

    def get_memory_by_key(self, key: str) -> Optional[MemoryItem]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM memories WHERE key = ?", (key,))
            row = cur.fetchone()
            if row:
                return self._row_to_memory(row)
            return None

    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cur.fetchone()
            if row:
                return self._row_to_memory(row)
            return None

    def list_memories(
        self,
        memory_type: Optional[MemoryType | str] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            if memory_type:
                type_str = memory_type.value if hasattr(memory_type, "value") else str(memory_type)
                cur.execute(
                    "SELECT * FROM memories WHERE type = ? ORDER BY updated_at DESC LIMIT ?",
                    (type_str, limit),
                )
            else:
                cur.execute("SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [self._row_to_memory(r) for r in rows]

    def delete_memory_by_key(self, key: str) -> bool:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM memories WHERE key = ?", (key,))
            conn.commit()
            return cur.rowcount > 0

    def record_access(self, memory_id: str, query: Optional[str] = None) -> None:
        now = time.time()
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
                (now, memory_id),
            )
            conn.execute(
                "INSERT INTO memory_access (id, memory_id, accessed_at, query) VALUES (hex(randomblob(8)), ?, ?, ?)",
                (memory_id, now, query),
            )
            conn.commit()

    def _row_to_memory(self, row: Any) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            type=MemoryType(row["type"]),
            key=row["key"],
            content=row["content"],
            metadata=json.loads(row["metadata_json"] or "{}"),
            source=row["source"],
            confidence=MemoryConfidence(row["confidence"]),
            importance=row["importance"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
            expires_at=row["expires_at"],
            privacy_level=PrivacyLevel(row["privacy_level"]),
            access_count=row["access_count"],
        )

    # --- Project CRUD ---

    def save_project(self, project: ProjectRecord) -> None:
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO projects (
                    project_id, name, path, description, status, tags_json, last_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.project_id,
                    project.name,
                    project.path,
                    project.description,
                    project.status,
                    json.dumps(project.tags),
                    project.last_used,
                ),
            )
            conn.commit()

    def get_project_by_name(self, name: str) -> Optional[ProjectRecord]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE LOWER(name) = LOWER(?)", (name,))
            row = cur.fetchone()
            if row:
                return ProjectRecord(
                    project_id=row["project_id"],
                    name=row["name"],
                    path=row["path"],
                    description=row["description"],
                    status=row["status"],
                    tags=json.loads(row["tags_json"] or "[]"),
                    last_used=row["last_used"],
                )
            return None

    def list_projects(self) -> List[ProjectRecord]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects ORDER BY last_used DESC")
            rows = cur.fetchall()
            return [
                ProjectRecord(
                    project_id=r["project_id"],
                    name=r["name"],
                    path=r["path"],
                    description=r["description"],
                    status=r["status"],
                    tags=json.loads(r["tags_json"] or "[]"),
                    last_used=r["last_used"],
                )
                for r in rows
            ]

    # --- Task CRUD ---

    def save_task(self, task: TaskRecord) -> None:
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks (
                    task_id, title, description, status, priority, project_id,
                    created_at, updated_at, due_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.title,
                    task.description,
                    task.status.value if hasattr(task.status, "value") else str(task.status),
                    task.priority,
                    task.project_id,
                    task.created_at,
                    task.updated_at,
                    task.due_at,
                ),
            )
            conn.commit()

    def list_tasks(self, status: Optional[TaskStatus | str] = None) -> List[TaskRecord]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            if status:
                st_str = status.value if hasattr(status, "value") else str(status)
                cur.execute("SELECT * FROM tasks WHERE status = ? ORDER BY priority ASC, updated_at DESC", (st_str,))
            else:
                cur.execute("SELECT * FROM tasks ORDER BY priority ASC, updated_at DESC")
            rows = cur.fetchall()
            return [
                TaskRecord(
                    task_id=r["task_id"],
                    title=r["title"],
                    description=r["description"],
                    status=TaskStatus(r["status"]),
                    priority=r["priority"],
                    project_id=r["project_id"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    due_at=r["due_at"],
                )
                for r in rows
            ]
