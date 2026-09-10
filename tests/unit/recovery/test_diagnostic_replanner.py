"""
Unit tests for DiagnosticReplanner.
"""

from jarvis.core.orchestration.plan import Plan, PlanStep
from jarvis.core.recovery.evidence import DiagnosticEvidence
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.replanner import DiagnosticReplanner
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause


def test_replan_with_candidate_path():
    replanner = DiagnosticReplanner()
    plan = Plan(
        plan_id="plan_1",
        goal_id="goal_1",
        steps=[
            PlanStep(step_id="step_1", tool_name="filesystem.read", arguments={"path": "missing.txt"}, description="Read missing file")
        ]
    )
    event = FailureEvent(execution_id="exec_1", step_id="step_1", tool_name="filesystem.read", error_message="File not found")
    rc = RootCause(category=FailureCategory.PATH_INVALID, confidence=ConfidenceLevel.LIKELY)
    evidence = DiagnosticEvidence(filesystem_state={"candidate_path": "C:\\found\\missing.txt"})

    new_plan = replanner.replan(plan, event, rc, evidence)
    assert new_plan is not None
    assert len(new_plan.steps) == 1
    assert new_plan.steps[0].arguments["path"] == "C:\\found\\missing.txt"
