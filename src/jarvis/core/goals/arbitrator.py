"""
Task & Goal Arbitration Layer for JARVIS.
Decides the next executable unit (Objective, Goal, or Workflow) based on priority, resources, and dependencies.
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from jarvis.core.goals.models import Goal, Objective, GoalStatus, ObjectiveStatus
from jarvis.core.goals.queue import BoundedGoalPriorityQueue
from jarvis.system.resource_arbitrator import ResourceArbitrator, ResourceType

logger = logging.getLogger("jarvis.core.goals.arbitrator")


class GoalArbitrator:
    """Arbitrates next executable unit across queued goals and system resource leases."""

    def __init__(
        self,
        queue: Optional[BoundedGoalPriorityQueue] = None,
        resource_arbitrator: Optional[ResourceArbitrator] = None,
    ):
        self.queue = queue or BoundedGoalPriorityQueue()
        self.resource_arbitrator = resource_arbitrator or ResourceArbitrator.get_instance()

    def arbitrate_next(self, current_user_command: Optional[str] = None) -> Optional[Tuple[Goal, Objective]]:
        """
        Selects the next ready (Goal, Objective) pair that satisfies:
        1. Queue precedence & starvation boost
        2. Objective dependency resolution
        3. Resource availability & lease preemption
        4. Blocker-free state
        """
        ordered_goals = self.queue.get_ordered_goals()
        if not ordered_goals:
            return None

        for goal in ordered_goals:
            if goal.status in (GoalStatus.PAUSED, GoalStatus.BLOCKED, GoalStatus.WAITING_FOR_USER):
                continue

            # Find next ready objective within goal
            ready_obj = self._find_ready_objective(goal)
            if ready_obj:
                # Check model resource availability for goal execution
                if self.resource_arbitrator.is_available(ResourceType.MODEL):
                    return (goal, ready_obj)
                else:
                    logger.debug(f"GoalArbitrator: MODEL resource currently leased; deferring goal '{goal.title}'")
                    continue

        return None

    def _find_ready_objective(self, goal: Goal) -> Optional[Objective]:
        completed_ids = {obj.objective_id for obj in goal.objectives if obj.status == ObjectiveStatus.COMPLETED}

        for obj in goal.objectives:
            if obj.status == ObjectiveStatus.PENDING:
                # Check if all dependencies are completed
                deps_met = all(dep_id in completed_ids for dep_id in obj.dependencies)
                if deps_met:
                    return obj

        return None
