"""
Unit tests for BoundedGoalPriorityQueue and GoalArbitrator.
"""

import time
import pytest
from jarvis.core.goals.models import Goal, GoalStatus, GoalPriority, GoalOwner
from jarvis.core.goals.policy import GoalPolicy
from jarvis.core.goals.queue import BoundedGoalPriorityQueue
from jarvis.core.goals.arbitrator import GoalArbitrator
from jarvis.core.goals.manager import GoalManager


def test_priority_queue_ordering():
    queue = BoundedGoalPriorityQueue(max_capacity=5)
    g_low = Goal(title="Low Goal", priority=GoalPriority.LOW, owner=GoalOwner.BACKGROUND_MONITOR)
    g_critical = Goal(title="Critical Goal", priority=GoalPriority.CRITICAL, owner=GoalOwner.USER)
    g_high = Goal(title="High Goal", priority=GoalPriority.HIGH, owner=GoalOwner.USER)

    g_low.status = GoalStatus.ACTIVE
    g_critical.status = GoalStatus.ACTIVE
    g_high.status = GoalStatus.ACTIVE

    queue.enqueue(g_low)
    queue.enqueue(g_high)
    queue.enqueue(g_critical)

    ordered = queue.get_ordered_goals()
    assert len(ordered) == 3
    assert ordered[0].title == "Critical Goal"
    assert ordered[1].title == "High Goal"
    assert ordered[2].title == "Low Goal"


def test_starvation_protection():
    queue = BoundedGoalPriorityQueue(max_capacity=5, starvation_threshold_sec=0.1)
    g_low = Goal(title="Waiting Low Goal", priority=GoalPriority.LOW, owner=GoalOwner.BACKGROUND_MONITOR)
    g_high = Goal(title="New High Goal", priority=GoalPriority.HIGH, owner=GoalOwner.USER)

    g_low.status = GoalStatus.ACTIVE
    g_high.status = GoalStatus.ACTIVE

    queue.enqueue(g_low)
    time.sleep(0.15)  # Trigger starvation threshold
    queue.enqueue(g_high)

    ordered = queue.get_ordered_goals()
    # Starvation boost elevates low goal score
    assert len(ordered) == 2


from jarvis.memory.database import DatabaseManager
from jarvis.core.goals.repository import GoalRepository


def test_goal_arbitrator(tmp_path):
    db_mgr = DatabaseManager(db_path=tmp_path / "test_arbitrator.db")
    repo = GoalRepository(db_manager=db_mgr)
    policy = GoalPolicy(max_active_goals=200)
    queue = BoundedGoalPriorityQueue(max_capacity=200)
    mgr = GoalManager(repository=repo, policy=policy, queue=queue)
    g = mgr.create_goal(title="Arbitration Goal", template_id="project_health")
    mgr.activate_goal(g.goal_id)

    arbitrator = GoalArbitrator(queue=mgr.queue)
    next_unit = arbitrator.arbitrate_next()
    assert next_unit is not None
    goal, obj = next_unit
    assert goal.goal_id == g.goal_id
    assert obj.title is not None
