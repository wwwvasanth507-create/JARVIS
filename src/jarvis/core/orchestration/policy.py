"""
Plan Validation and Safety Policy Enforcement for JARVIS.
"""

from typing import Any, Dict, List, Optional
from jarvis.core.orchestration.errors import PlanValidationError
from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.security.permissions import PermissionEvaluator, PermissionCheckResult, RiskLevel


class PlanValidator:
    """Validates proposed plans before execution."""

    PROHIBITED_COMBINATIONS = [
        ("filesystem.read_file", "shell.execute"),
    ]

    def __init__(self, permission_evaluator: Optional[PermissionEvaluator] = None):
        self.evaluator = permission_evaluator or PermissionEvaluator()

    def validate(self, plan: Plan, available_tools: Dict[str, Any]) -> List[PermissionCheckResult]:
        results = []
        step_ids = {s.step_id for s in plan.steps}

        tool_sequence = [s.tool_name for s in plan.steps]

        # Check prohibited tool combination sequence
        for i in range(len(tool_sequence) - 1):
            pair = (tool_sequence[i], tool_sequence[i + 1])
            if pair in self.PROHIBITED_COMBINATIONS:
                raise PlanValidationError(
                    message=f"Prohibited tool combination sequence detected: {pair}",
                    violations=["prohibited_combination"],
                )

        for step in plan.steps:
            # 1. Validate tool existence
            if step.tool_name not in available_tools:
                raise PlanValidationError(
                    message=f"Tool '{step.tool_name}' is not registered in the system.",
                    step_id=step.step_id,
                    violations=["unregistered_tool"],
                )

            # 2. Validate dependencies
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise PlanValidationError(
                        message=f"Step '{step.step_id}' references unknown dependency '{dep}'.",
                        step_id=step.step_id,
                        violations=["invalid_dependency"],
                    )

            # 3. Evaluate permission & risk
            eval_result = self.evaluator.evaluate(
                category=step.permission,
                risk_level=step.risk_level,
                action_name=step.tool_name,
                parameters=step.arguments,
            )
            if not eval_result.allowed:
                raise PlanValidationError(
                    message=f"Step '{step.step_id}' ({step.tool_name}) rejected by permission policy: {eval_result.reason}",
                    step_id=step.step_id,
                    violations=[eval_result.reason],
                )

            results.append(eval_result)

        return results
