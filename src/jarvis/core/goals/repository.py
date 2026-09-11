"""
SQLite Persistence Repository for JARVIS Goal Subsystem.
"""

import json
import time
import logging
from typing import List, Optional, Dict, Any
from jarvis.core.goals.models import (
    Goal,
    GoalStatus,
    GoalPriority,
    AutonomyLevel,
    DeadlineType,
    GoalOwner,
    ProgressConfidence,
    Objective,
    ObjectiveStatus,
    GoalCheckpoint,
)
from jarvis.memory.database import DatabaseManager
from jarvis.memory.migrations import SchemaMigrator
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.core.goals.repository")


class GoalRepository:
    """Manages SQLite storage for goals, objectives, checkpoints, and logs."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_mgr = db_manager or DatabaseManager()
        migrator = SchemaMigrator(self.db_mgr)
        migrator.migrate()

    def create_goal(self, goal: Goal) -> Goal:
        now = time.time()
        goal.created_at = now
        goal.updated_at = now
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO goals (
                    goal_id, title, description, owner, created_at, updated_at, status, priority,
                    deadline, deadline_type, time_window_json, constraints_json, dependencies_json,
                    success_criteria_json, risk_level, resource_budget_json, progress, progress_confidence,
                    autonomy_level, associated_project, associated_memories_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.goal_id,
                    goal.title,
                    goal.description,
                    goal.owner.value,
                    goal.created_at,
                    goal.updated_at,
                    goal.status.value,
                    goal.priority.value,
                    goal.deadline,
                    goal.deadline_type.value,
                    json.dumps(goal.time_window),
                    json.dumps(goal.constraints),
                    json.dumps(goal.dependencies),
                    json.dumps(goal.success_criteria),
                    goal.risk_level.value,
                    json.dumps(goal.resource_budget),
                    goal.progress,
                    goal.progress_confidence.value,
                    int(goal.autonomy_level),
                    goal.associated_project,
                    json.dumps(goal.associated_memories),
                ),
            )
            conn.commit()

        for obj in goal.objectives:
            self.create_objective(obj)

        self.log_event(goal.goal_id, "GOAL_CREATED", f"Goal '{goal.title}' created.")
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM goals WHERE goal_id = ?", (goal_id,))
            row = cur.fetchone()
            if not row:
                return None

        goal = self._row_to_goal(row)
        goal.objectives = self.list_objectives(goal_id)
        return goal

    def update_goal(self, goal: Goal) -> Goal:
        goal.updated_at = time.time()
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                UPDATE goals SET
                    title = ?, description = ?, owner = ?, updated_at = ?, status = ?, priority = ?,
                    deadline = ?, deadline_type = ?, time_window_json = ?, constraints_json = ?,
                    dependencies_json = ?, success_criteria_json = ?, risk_level = ?, resource_budget_json = ?,
                    progress = ?, progress_confidence = ?, autonomy_level = ?, associated_project = ?,
                    associated_memories_json = ?
                WHERE goal_id = ?
                """,
                (
                    goal.title,
                    goal.description,
                    goal.owner.value,
                    goal.updated_at,
                    goal.status.value,
                    goal.priority.value,
                    goal.deadline,
                    goal.deadline_type.value,
                    json.dumps(goal.time_window),
                    json.dumps(goal.constraints),
                    json.dumps(goal.dependencies),
                    json.dumps(goal.success_criteria),
                    goal.risk_level.value,
                    json.dumps(goal.resource_budget),
                    goal.progress,
                    goal.progress_confidence.value,
                    int(goal.autonomy_level),
                    goal.associated_project,
                    json.dumps(goal.associated_memories),
                    goal.goal_id,
                ),
            )
            conn.commit()
        return goal

    def delete_goal(self, goal_id: str) -> bool:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
            conn.commit()
            return cur.rowcount > 0

    def list_goals(
        self,
        status: Optional[GoalStatus] = None,
        owner: Optional[GoalOwner] = None,
        priority: Optional[GoalPriority] = None,
        project: Optional[str] = None,
        limit: int = 100,
    ) -> List[Goal]:
        query = "SELECT * FROM goals WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if owner:
            query += " AND owner = ?"
            params.append(owner.value)
        if priority:
            query += " AND priority = ?"
            params.append(priority.value)
        if project:
            query += " AND associated_project = ?"
            params.append(project)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

        goals = []
        for r in rows:
            g = self._row_to_goal(r)
            g.objectives = self.list_objectives(g.goal_id)
            goals.append(g)
        return goals

    def create_objective(self, obj: Objective) -> Objective:
        now = time.time()
        obj.created_at = now
        obj.updated_at = now
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO objectives (
                    objective_id, goal_id, title, description, status, dependencies_json,
                    completion_criteria_json, verification_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    obj.objective_id,
                    obj.goal_id,
                    obj.title,
                    obj.description,
                    obj.status.value,
                    json.dumps(obj.dependencies),
                    json.dumps(obj.completion_criteria),
                    json.dumps(obj.verification),
                    obj.created_at,
                    obj.updated_at,
                ),
            )
            conn.commit()
        return obj

    def update_objective(self, obj: Objective) -> Objective:
        obj.updated_at = time.time()
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                UPDATE objectives SET
                    title = ?, description = ?, status = ?, dependencies_json = ?,
                    completion_criteria_json = ?, verification_json = ?, updated_at = ?
                WHERE objective_id = ?
                """,
                (
                    obj.title,
                    obj.description,
                    obj.status.value,
                    json.dumps(obj.dependencies),
                    json.dumps(obj.completion_criteria),
                    json.dumps(obj.verification),
                    obj.updated_at,
                    obj.objective_id,
                ),
            )
            conn.commit()
        return obj

    def list_objectives(self, goal_id: str) -> List[Objective]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM objectives WHERE goal_id = ? ORDER BY created_at ASC", (goal_id,))
            rows = cur.fetchall()

        objs = []
        for r in rows:
            objs.append(
                Objective(
                    objective_id=r[0],
                    goal_id=r[1],
                    title=r[2],
                    description=r[3] or "",
                    status=ObjectiveStatus(r[4]),
                    dependencies=json.loads(r[5] or "[]"),
                    completion_criteria=json.loads(r[6] or "[]"),
                    verification=json.loads(r[7] or "{}"),
                    created_at=r[8],
                    updated_at=r[9],
                )
            )
        return objs

    def save_checkpoint(self, checkpoint: GoalCheckpoint) -> GoalCheckpoint:
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO goal_checkpoints (
                    checkpoint_id, goal_id, state_json, verified_outputs_json, blockers_json,
                    resource_usage_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.goal_id,
                    json.dumps(checkpoint.state),
                    json.dumps(checkpoint.verified_outputs),
                    json.dumps(checkpoint.blockers),
                    json.dumps(checkpoint.resource_usage),
                    checkpoint.created_at,
                ),
            )
            conn.commit()
        return checkpoint

    def get_latest_checkpoint(self, goal_id: str) -> Optional[GoalCheckpoint]:
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM goal_checkpoints WHERE goal_id = ? ORDER BY created_at DESC LIMIT 1", (goal_id,))
            r = cur.fetchone()
            if not r:
                return None
            return GoalCheckpoint(
                checkpoint_id=r[0],
                goal_id=r[1],
                state=json.loads(r[2] or "{}"),
                verified_outputs=json.loads(r[3] or "[]"),
                blockers=json.loads(r[4] or "[]"),
                resource_usage=json.loads(r[5] or "{}"),
                created_at=r[6],
            )

    def log_event(self, goal_id: str, event_type: str, description: str, data: Optional[Dict[str, Any]] = None) -> None:
        log_id = f"log_{int(time.time() * 1000)}"
        with self.db_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO goal_logs (log_id, goal_id, event_type, description, data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (log_id, goal_id, event_type, description, json.dumps(data or {}), time.time()),
            )
            conn.commit()

    def _row_to_goal(self, r: Any) -> Goal:
        return Goal(
            goal_id=r[0],
            title=r[1],
            description=r[2] or "",
            owner=GoalOwner(r[3]),
            created_at=r[4],
            updated_at=r[5],
            status=GoalStatus(r[6]),
            priority=GoalPriority(r[7]),
            deadline=r[8],
            deadline_type=DeadlineType(r[9]),
            time_window=json.loads(r[10] or "{}"),
            constraints=json.loads(r[11] or "{}"),
            dependencies=json.loads(r[12] or "[]"),
            success_criteria=json.loads(r[13] or "[]"),
            risk_level=RiskLevel(r[14]),
            resource_budget=json.loads(r[15] or "{}"),
            progress=r[16],
            progress_confidence=ProgressConfidence(r[17]),
            autonomy_level=AutonomyLevel(r[18]),
            associated_project=r[19],
            associated_memories=json.loads(r[20] or "[]"),
        )
