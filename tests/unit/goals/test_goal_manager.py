import pytest
from jarvis.core.goals.models import GoalPriority, AutonomyLevel, GoalStatus
from jarvis.memory.database import DatabaseManager
from jarvis.core.goals.repository import GoalRepository
from jarvis.core.goals.policy import GoalPolicy
from jarvis.core.goals.queue import BoundedGoalPriorityQueue
from jarvis.core.goals.manager import GoalManager


@pytest.fixture
def mgr(tmp_path):
    db_mgr = DatabaseManager(db_path=tmp_path / "test_goals.db")
    repo = GoalRepository(db_manager=db_mgr)
    policy = GoalPolicy(max_active_goals=200)
    queue = BoundedGoalPriorityQueue(max_capacity=200)
    return GoalManager(repository=repo, policy=policy, queue=queue)


def test_goal_creation_and_activation(mgr):
    goal = mgr.create_goal(
        title="Maintain Project Health",
        description="Run test suite periodically",
        priority=GoalPriority.HIGH,
        autonomy_level=AutonomyLevel.LEVEL_2_SUPERVISED,
        template_id="project_health",
    )
    assert goal.goal_id is not None
    assert goal.status == GoalStatus.DRAFT
    assert len(goal.objectives) > 0

    active_g = mgr.activate_goal(goal.goal_id)
    assert active_g.status == GoalStatus.ACTIVE


def test_goal_pause_resume_cancel(mgr):
    goal = mgr.create_goal(title="Test Workflow Goal")
    mgr.activate_goal(goal.goal_id)

    paused = mgr.pause_goal(goal.goal_id)
    assert paused.status == GoalStatus.PAUSED

    resumed = mgr.resume_goal(goal.goal_id)
    assert resumed.status == GoalStatus.ACTIVE

    cancelled = mgr.cancel_goal(goal.goal_id)
    assert cancelled.status == GoalStatus.CANCELLED


def test_goal_progress_and_explain(mgr):
    goal = mgr.create_goal(title="Weekly Report", template_id="weekly_report")
    mgr.activate_goal(goal.goal_id)

    prog = mgr.get_goal_progress(goal.goal_id)
    assert prog.goal_id == goal.goal_id
    assert prog.health_score >= 0.0

    exp = mgr.explain_goal(goal.goal_id)
    assert exp["title"] == "Weekly Report"
    assert "explanation" in exp


def test_goal_proposal_generation(mgr):
    prop = mgr.propose_goal_from_intent("Help me test my project and report failures")
    assert "proposed_title" in prop
    assert len(prop["objectives"]) > 0


def test_goal_startup_reconciliation(mgr):
    g = mgr.create_goal(title="Persistent Monitoring Goal")
    mgr.activate_goal(g.goal_id)

    reconciled = mgr.reconcile_goals_on_startup()
    assert any(item.goal_id == g.goal_id for item in reconciled)
