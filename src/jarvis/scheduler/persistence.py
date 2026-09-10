"""
SQLite Persistence Manager for JARVIS Scheduler.
Manages scheduled_tasks and task_runs database tables.
"""

import json
import sqlite3
import logging
from typing import List, Optional, Dict, Any
from jarvis.memory.database import DatabaseManager
from jarvis.scheduler.models import ScheduledTask, TaskRun, TaskState

logger = logging.getLogger("jarvis.scheduler.persistence")


class TaskPersistence:
    """Handles SQLite persistence for scheduled tasks and execution run history."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            task_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            action TEXT,
            skill_id TEXT,
            tool_name TEXT,
            arguments TEXT,
            schedule TEXT,
            timezone TEXT,
            status TEXT NOT NULL,
            priority INTEGER,
            risk_level TEXT,
            enabled INTEGER,
            created_at REAL,
            updated_at REAL,
            next_run_at REAL,
            last_run_at REAL,
            last_result TEXT,
            failure_count INTEGER,
            is_recurring INTEGER,
            notification_type TEXT
        );

        CREATE TABLE IF NOT EXISTS task_runs (
            run_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            started_at REAL NOT NULL,
            finished_at REAL,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            verification_result TEXT,
            recovery_attempts INTEGER,
            FOREIGN KEY (task_id) REFERENCES scheduled_tasks (task_id) ON DELETE CASCADE
        );
        """
        self.db.execute_script(sql)

    def save_task(self, task: ScheduledTask) -> None:
        conn = self.db.get_connection()
        sql = """
        INSERT OR REPLACE INTO scheduled_tasks (
            task_id, name, description, action, skill_id, tool_name, arguments,
            schedule, timezone, status, priority, risk_level, enabled,
            created_at, updated_at, next_run_at, last_run_at, last_result,
            failure_count, is_recurring, notification_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with conn:
            conn.execute(
                sql,
                (
                    task.task_id,
                    task.name,
                    task.description,
                    task.action,
                    task.skill_id,
                    task.tool_name,
                    json.dumps(task.arguments),
                    task.schedule,
                    task.timezone,
                    task.status.value,
                    int(task.priority),
                    task.risk_level.value,
                    1 if task.enabled else 0,
                    task.created_at,
                    task.updated_at,
                    task.next_run_at,
                    task.last_run_at,
                    json.dumps(task.last_result) if task.last_result else None,
                    task.failure_count,
                    1 if task.is_recurring else 0,
                    task.notification_type,
                )
            )

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM scheduled_tasks WHERE task_id = ?;", (task_id,)).fetchone()
        if not row:
            return None
        return self._row_to_task(row)

    def list_tasks(self, include_disabled: bool = False) -> List[ScheduledTask]:
        conn = self.db.get_connection()
        query = "SELECT * FROM scheduled_tasks;" if include_disabled else "SELECT * FROM scheduled_tasks WHERE enabled = 1;"
        rows = conn.execute(query).fetchall()
        return [self._row_to_task(r) for r in rows]

    def delete_task(self, task_id: str) -> bool:
        conn = self.db.get_connection()
        with conn:
            cur = conn.execute("DELETE FROM scheduled_tasks WHERE task_id = ?;", (task_id,))
            return cur.rowcount > 0

    def save_run(self, run: TaskRun) -> None:
        conn = self.db.get_connection()
        sql = """
        INSERT OR REPLACE INTO task_runs (
            run_id, task_id, started_at, finished_at, status, result, error,
            verification_result, recovery_attempts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        with conn:
            conn.execute(
                sql,
                (
                    run.run_id,
                    run.task_id,
                    run.started_at,
                    run.finished_at,
                    run.status.value,
                    json.dumps(run.result) if run.result else None,
                    run.error,
                    json.dumps(run.verification_result) if run.verification_result else None,
                    run.recovery_attempts,
                )
            )

    def list_runs(self, task_id: Optional[str] = None, limit: int = 50) -> List[TaskRun]:
        conn = self.db.get_connection()
        if task_id:
            query = "SELECT * FROM task_runs WHERE task_id = ? ORDER BY started_at DESC LIMIT ?;"
            rows = conn.execute(query, (task_id, limit)).fetchall()
        else:
            query = "SELECT * FROM task_runs ORDER BY started_at DESC LIMIT ?;"
            rows = conn.execute(query, (limit,)).fetchall()
        return [self._row_to_run(r) for r in rows]

    def _row_to_task(self, row: sqlite3.Row) -> ScheduledTask:
        d = dict(row)
        return ScheduledTask(
            task_id=d["task_id"],
            name=d["name"],
            description=d.get("description") or "",
            action=d.get("action") or "",
            skill_id=d.get("skill_id"),
            tool_name=d.get("tool_name"),
            arguments=json.loads(d["arguments"]) if d.get("arguments") else {},
            schedule=d.get("schedule") or "",
            timezone=d.get("timezone") or "UTC",
            status=TaskState(d["status"]),
            priority=d.get("priority", 2),
            risk_level=d.get("risk_level", "LOW"),
            enabled=bool(d["enabled"]),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            next_run_at=d.get("next_run_at"),
            last_run_at=d.get("last_run_at"),
            last_result=json.loads(d["last_result"]) if d.get("last_result") else None,
            failure_count=d.get("failure_count", 0),
            is_recurring=bool(d.get("is_recurring", 0)),
            notification_type=d.get("notification_type") or "TEXT",
        )

    def _row_to_run(self, row: sqlite3.Row) -> TaskRun:
        d = dict(row)
        return TaskRun(
            run_id=d["run_id"],
            task_id=d["task_id"],
            started_at=d["started_at"],
            finished_at=d.get("finished_at"),
            status=TaskState(d["status"]),
            result=json.loads(d["result"]) if d.get("result") else None,
            error=d.get("error"),
            verification_result=json.loads(d["verification_result"]) if d.get("verification_result") else None,
            recovery_attempts=d.get("recovery_attempts", 0),
        )
