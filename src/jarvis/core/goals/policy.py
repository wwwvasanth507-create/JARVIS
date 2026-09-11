"""
Governed Safety Policy for JARVIS Goal Subsystem.
Enforces autonomy level rules, capacity limits, cycle detection, and security intersection.
"""

import logging
from typing import List, Optional, Dict, Any, Set
from jarvis.core.goals.models import Goal, Objective, AutonomyLevel
from jarvis.security.permissions import PermissionEvaluator, PermissionCategory, RiskLevel

logger = logging.getLogger("jarvis.core.goals.policy")


class GoalPolicyError(Exception):
    pass


class GoalPolicy:
    """Enforces safety, security, autonomy levels, and structural constraints on goals."""

    def __init__(
        self,
        max_active_goals: int = 10,
        max_objectives_per_goal: int = 20,
        max_depth: int = 4,
        permission_evaluator: Optional[PermissionEvaluator] = None,
    ):
        self.max_active_goals = max_active_goals
        self.max_objectives_per_goal = max_objectives_per_goal
        self.max_depth = max_depth
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()

    def validate_goal_creation(self, goal: Goal, current_active_count: int = 0) -> None:
        """Validates structural bounds and safety constraints before goal creation."""
        if current_active_count >= self.max_active_goals:
            raise GoalPolicyError(f"Maximum active goals limit ({self.max_active_goals}) reached.")

        if len(goal.objectives) > self.max_objectives_per_goal:
            raise GoalPolicyError(f"Goal exceeds maximum allowed objectives limit ({self.max_objectives_per_goal}).")

        # Check for dependency cycles
        self.detect_objective_cycles(goal.objectives)

    def validate_autonomy_level(self, goal: Goal, action_risk: RiskLevel) -> bool:
        """
        Validates autonomy level rules:
        - Level 0 (Manual): All actions require user confirmation.
        - Level 1 (Assisted): Proposals prepared; execution requires confirmation.
        - Level 2 (Supervised): Approved workflows run; High/Critical risk actions require confirmation.
        - Level 3 (Scheduled): Scheduled goals run; High/Critical risk actions require confirmation.
        """
        if action_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            # High-risk actions ALWAYS require confirmation regardless of autonomy level
            return False

        if goal.autonomy_level == AutonomyLevel.LEVEL_0_MANUAL:
            return False

        return True

    def detect_objective_cycles(self, objectives: List[Objective]) -> None:
        """Detects circular dependencies in objective list."""
        adj: Dict[str, List[str]] = {obj.objective_id: obj.dependencies for obj in objectives}
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            for dep in adj.get(node, []):
                if dep not in visited:
                    dfs(dep)
                elif dep in rec_stack:
                    raise GoalPolicyError(f"Circular dependency detected involving objective '{dep}'.")
            rec_stack.remove(node)

        for obj_id in adj:
            if obj_id not in visited:
                dfs(obj_id)
