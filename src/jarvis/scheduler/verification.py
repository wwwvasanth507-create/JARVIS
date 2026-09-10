"""
Task Run Verification for JARVIS Scheduler.
"""

from typing import Dict, Any, Optional
from jarvis.core.orchestration.verification import VerificationManager
from jarvis.scheduler.models import TaskRun, TaskState


class TaskVerification:
    """Verifies scheduled task execution outcomes."""

    def __init__(self, verification_mgr: Optional[VerificationManager] = None):
        self.verification_mgr = verification_mgr or VerificationManager()

    def verify_run(self, run: TaskRun) -> Dict[str, Any]:
        """Returns structured verification result dictionary."""
        success = (run.status == TaskState.COMPLETED)
        return {
            "run_id": run.run_id,
            "task_id": run.task_id,
            "verified": success,
            "error": run.error if not success else None,
        }
