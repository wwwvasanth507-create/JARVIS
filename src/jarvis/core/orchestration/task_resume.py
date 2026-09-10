"""
Interrupted Task State Persistence & Safe Resume Manager for JARVIS.

Handles safe task interruption, checkpointing, post-restart inspection, and user resume/abort protocol.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.utils.paths import ResourcePathResolver

logger = logging.getLogger(__name__)

CACHE_FILE = ResourcePathResolver.get_cache_dir() / "interrupted_tasks.json"


class TaskCheckpoint(BaseModel):
    execution_id: str
    task_id: Optional[str] = None
    request: str
    goal: str
    completed_steps: List[Dict[str, Any]] = Field(default_factory=list)
    pending_steps: List[Dict[str, Any]] = Field(default_factory=list)
    completed_step_indices: List[int] = Field(default_factory=list)
    timestamp: float
    is_safe_to_resume: bool = True


class TaskResumeManager:
    """Manages checkpointing and resume of interrupted multi-step workflows."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_file = Path(storage_path) if storage_path else CACHE_FILE

    @classmethod
    def checkpoint_task(cls, execution_id: str, request: str, goal: str, completed_steps: List[Any], pending_steps: List[Any], is_safe: bool = True, target_file: Optional[Path] = None, completed_step_indices: Optional[List[int]] = None) -> TaskCheckpoint:
        file_path = target_file or CACHE_FILE
        cp = TaskCheckpoint(
            execution_id=execution_id,
            task_id=execution_id,
            request=request,
            goal=goal,
            completed_steps=[s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in completed_steps],
            pending_steps=[s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in pending_steps],
            completed_step_indices=completed_step_indices or [],
            timestamp=Path(file_path).stat().st_mtime if file_path.exists() else 0.0,
            is_safe_to_resume=is_safe
        )

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([cp.model_dump()], f, indent=2)
            logger.info(f"TaskCheckpoint saved for execution {execution_id}.")
        except Exception as e:
            logger.warning(f"Failed to save task checkpoint: {e}")

        return cp

    def create_checkpoint(self, task_id: str, plan: Any, completed_step_indices: List[int]) -> TaskCheckpoint:
        steps = getattr(plan, "steps", [])
        completed = [steps[i] for i in completed_step_indices if i < len(steps)]
        pending = [s for i, s in enumerate(steps) if i not in completed_step_indices]
        return self.checkpoint_task(
            execution_id=task_id,
            request=getattr(plan, "goal_id", "task"),
            goal=getattr(plan, "goal_id", "goal"),
            completed_steps=completed,
            pending_steps=pending,
            completed_step_indices=completed_step_indices,
            target_file=self.storage_file
        )

    def get_pending_resumes(self) -> List[TaskCheckpoint]:
        cp = self.get_interrupted_task(target_file=self.storage_file)
        if cp:
            return [cp]
        return []

    @classmethod
    def get_interrupted_task(cls, target_file: Optional[Path] = None) -> Optional[TaskCheckpoint]:
        """Inspects disk cache for interrupted task checkpoints post-restart."""
        file_path = target_file or CACHE_FILE
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return TaskCheckpoint(**data[0])
        except Exception as e:
            logger.warning(f"Error reading interrupted task checkpoint: {e}")
        return None

    @classmethod
    def clear_checkpoint(cls, target_file: Optional[Path] = None) -> None:
        """Clears persisted task checkpoint after task completion or abort."""
        file_path = target_file or CACHE_FILE
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info("Task checkpoint cleared.")
            except Exception as e:
                logger.warning(f"Error clearing task checkpoint: {e}")
