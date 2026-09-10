"""
Diagnostic Replanner for JARVIS recovery.
Constructs revised plans incorporating diagnostic evidence while respecting permission boundaries.
"""

import logging
from typing import Optional, List, Any
from jarvis.core.recovery.evidence import DiagnosticEvidence
from jarvis.core.recovery.failure import FailureEvent
from jarvis.core.recovery.root_cause import RootCause
from jarvis.security.permissions import RiskLevel

logger = logging.getLogger("jarvis.core.recovery.replanner")


class DiagnosticReplanner:
    """Generates revised execution plans based on diagnostic findings."""

    def replan(
        self,
        original_plan: Plan,
        event: FailureEvent,
        root_cause: RootCause,
        evidence: DiagnosticEvidence
    ) -> Optional[Plan]:
        """
        Builds a modified plan incorporating diagnostic evidence.
        """
        from jarvis.core.orchestration.plan import Plan, PlanStep

        if not original_plan or not original_plan.steps:
            return None

        new_steps: List[PlanStep] = []
        for step in original_plan.steps:
            if step.step_id == event.step_id:
                # Add diagnostic adjustment step if filesystem candidate path found
                if evidence.filesystem_state and evidence.filesystem_state.get("candidate_path"):
                    candidate = evidence.filesystem_state["candidate_path"]
                    adj_args = dict(step.arguments)
                    adj_args["path"] = candidate
                    new_steps.append(
                        PlanStep(
                            step_id=f"{step.step_id}_replan",
                            tool_name=step.tool_name,
                            arguments=adj_args,
                            description=f"{step.description} (using candidate path '{candidate}')",
                            risk_level=step.risk_level,
                        )
                    )
                    continue

                # Default fallback step retry
                new_steps.append(
                    PlanStep(
                        step_id=f"{step.step_id}_replan",
                        tool_name=step.tool_name,
                        arguments=step.arguments,
                        description=f"{step.description} (replanned)",
                        risk_level=step.risk_level,
                    )
                )
            else:
                new_steps.append(step)

        return Plan(
            plan_id=f"{original_plan.plan_id}_replan",
            goal_id=original_plan.goal_id,
            steps=new_steps,
        )
