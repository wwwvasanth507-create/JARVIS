"""
Deterministic Bounded Priority Queue with Starvation Protection for JARVIS Goals.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from jarvis.core.goals.models import Goal, GoalStatus, GoalPriority, GoalOwner

logger = logging.getLogger("jarvis.core.goals.queue")


class BoundedGoalPriorityQueue:
    """
    Governed priority queue for active goals and tasks.
    Precedence:
    1. Direct Boss/User Request (Highest)
    2. Critical Deadline Goals
    3. High-Priority User Goals
    4. Scheduled Tasks
    5. Background Monitoring Goals
    6. Low-Priority Maintenance (Lowest)
    """

    def __init__(self, max_capacity: int = 10, starvation_threshold_sec: float = 300.0):
        self.max_capacity = max_capacity
        self.starvation_threshold_sec = starvation_threshold_sec
        self._goals: Dict[str, Goal] = {}
        self._enqueue_times: Dict[str, float] = {}

    def enqueue(self, goal: Goal) -> bool:
        """Enqueues a goal if queue capacity is not exceeded."""
        if len(self._goals) >= self.max_capacity and goal.goal_id not in self._goals:
            logger.warning(f"Goal queue capacity ({self.max_capacity}) reached. Denied goal '{goal.title}'.")
            return False

        now = time.time()
        self._goals[goal.goal_id] = goal
        if goal.goal_id not in self._enqueue_times:
            self._enqueue_times[goal.goal_id] = now
        return True

    def remove(self, goal_id: str) -> Optional[Goal]:
        self._enqueue_times.pop(goal_id, None)
        return self._goals.pop(goal_id, None)

    def peek_next(self, current_user_command: Optional[str] = None) -> Optional[Goal]:
        """Returns the next highest-priority executable goal with starvation protection."""
        ordered = self.get_ordered_goals()
        return ordered[0] if ordered else None

    def get_ordered_goals(self) -> List[Goal]:
        """Sorts enqueued goals by priority rank, deadline urgency, starvation boost, and owner."""
        now = time.time()

        def compute_score(goal: Goal) -> float:
            score = float(goal.priority.rank * 100)

            # Owner boost
            if goal.owner == GoalOwner.USER:
                score += 500.0
            elif goal.owner == GoalOwner.SCHEDULED:
                score += 300.0

            # Deadline urgency boost
            if goal.deadline is not None:
                time_remaining = goal.deadline - now
                if time_remaining <= 0:
                    score += 400.0  # Overdue
                elif time_remaining < 3600:
                    score += 200.0  # Approaching within hour

            # Starvation protection boost
            enqueued_at = self._enqueue_times.get(goal.goal_id, now)
            wait_time = now - enqueued_at
            if wait_time > self.starvation_threshold_sec:
                starvation_boost = min(300.0, (wait_time / self.starvation_threshold_sec) * 50.0)
                score += starvation_boost

            return score

        # Filter out inactive goals
        active = [g for g in self._goals.values() if g.status in (GoalStatus.ACTIVE, GoalStatus.AT_RISK)]
        active.sort(key=compute_score, reverse=True)
        return active

    def clear(self) -> None:
        self._goals.clear()
        self._enqueue_times.clear()

    def __len__(self) -> int:
        return len(self._goals)
