"""
Plan Executor for JARVIS orchestration.
"""

import time
from typing import Any, Dict, Optional
from jarvis.core.orchestration.confirmation import ConfirmationManager
from jarvis.core.orchestration.dispatcher import ToolDispatcher
from jarvis.core.orchestration.errors import ConfirmationRequiredError, ExecutionFailedError, VerificationFailedError
from jarvis.core.orchestration.observation import ObservationManager
from jarvis.core.orchestration.plan import Plan, PlanStep, PlanStepStatus
from jarvis.core.orchestration.recovery import RecoveryManager
from jarvis.core.orchestration.state import ExecutionState, ExecutionStatus
from jarvis.core.orchestration.verification import VerificationManager
from jarvis.security.permissions import RiskLevel


class PlanExecutor:
    """Executes validated plan steps with observation, verification, and recovery."""

    def __init__(
        self,
        dispatcher: Optional[ToolDispatcher] = None,
        observation_mgr: Optional[ObservationManager] = None,
        verification_mgr: Optional[VerificationManager] = None,
        confirmation_mgr: Optional[ConfirmationManager] = None,
        recovery_mgr: Optional[RecoveryManager] = None,
    ):
        self.dispatcher = dispatcher or ToolDispatcher()
        self.observation_mgr = observation_mgr or ObservationManager()
        self.verification_mgr = verification_mgr or VerificationManager()
        self.confirmation_mgr = confirmation_mgr or ConfirmationManager()
        self.recovery_mgr = recovery_mgr or RecoveryManager()

    def execute_plan(
        self,
        plan: Plan,
        state: ExecutionState,
        confirmation_token: Optional[str] = None,
    ) -> ExecutionState:
        state.status = ExecutionStatus.EXECUTING
        state.plan = plan

        confirmed_steps = set()
        while True:
            # 1. Check if any step is WAITING_FOR_CONFIRMATION
            for step in plan.steps:
                if step.status == PlanStepStatus.WAITING_FOR_CONFIRMATION:
                    valid, pending, msg = self.confirmation_mgr.validate_confirmation(confirmation_token)
                    if valid:
                        step.status = PlanStepStatus.PENDING
                        state.status = ExecutionStatus.EXECUTING
                        state.confirmation_token = None
                        confirmed_steps.add(step.step_id)
                    else:
                        state.status = ExecutionStatus.WAITING_FOR_CONFIRMATION
                        return state

            ready_steps = plan.get_ready_steps()
            if not ready_steps:
                break

            for step in ready_steps:
                # 2. Check if high-risk step requires confirmation
                if step.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) and step.step_id not in confirmed_steps:
                    valid, pending, msg = self.confirmation_mgr.validate_confirmation(confirmation_token)
                    if valid:
                        confirmed_steps.add(step.step_id)
                    else:
                        pending_item = self.confirmation_mgr.request_confirmation(
                            action=step.tool_name,
                            arguments=step.arguments,
                            description=step.description,
                            risk_level=step.risk_level.value,
                        )
                        state.status = ExecutionStatus.WAITING_FOR_CONFIRMATION
                        state.confirmation_token = pending_item.token
                        step.status = PlanStepStatus.WAITING_FOR_CONFIRMATION
                        state.current_step = step
                        return state

                # 3. Execute step
                step.status = PlanStepStatus.EXECUTING
                state.current_step = step

                t0 = time.time()
                tool_res = self.dispatcher.dispatch(step.tool_name, step.arguments)
                tool_res.duration_ms = (time.time() - t0) * 1000.0

                # 3. Collect Observation
                obs = self.observation_mgr.observe(step.tool_name, step.arguments, tool_res)
                state.observations.append(obs)

                # 4. Verify post-condition
                tool_obj = self.dispatcher.get_tool(step.tool_name)
                verified, v_details = self.verification_mgr.verify_step(tool_obj, step.arguments, tool_res)
                state.verification_results.append(v_details)

                if verified:
                    step.status = PlanStepStatus.COMPLETED
                    step.result = tool_res.data
                    state.completed_steps.append(step)
                else:
                    step.error = v_details.get("reason", "Verification failed")
                    self.recovery_mgr.track_action(step.tool_name, step.arguments, step.error)

                    if self.recovery_mgr.can_retry_step(step):
                        self.recovery_mgr.record_step_retry(step)
                        # Re-attempt step on next loop iteration
                        step.status = PlanStepStatus.PENDING
                        continue
                    else:
                        step.status = PlanStepStatus.FAILED
                        state.failed_steps.append(step)
                        state.status = ExecutionStatus.FAILED
                        state.error = f"Step '{step.description}' failed verification: {step.error}"
                        return state

        # Check final plan status
        if all(s.status == PlanStepStatus.COMPLETED for s in plan.steps):
            state.status = ExecutionStatus.COMPLETED
            state.end_time = time.time()
        elif any(s.status == PlanStepStatus.FAILED for s in plan.steps):
            state.status = ExecutionStatus.FAILED
            state.end_time = time.time()

        return state
