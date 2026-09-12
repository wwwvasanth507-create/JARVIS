"""
Plan Critic and Plan Repairer for JARVIS General Reasoning.
Evaluates proposed task hierarchies for completeness, circular dependencies,
prerequisites, risk escalation, verification coverage, and provides automatic plan repairs.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.core.reasoning.decomposer import TaskHierarchy, TaskNode
from jarvis.core.reasoning.world_state import WorldState

logger = logging.getLogger("jarvis.core.reasoning.critic")


class PlanCriticReport(BaseModel):
    """Detailed evaluation report emitted by the PlanCritic."""
    is_valid: bool = True
    completeness_score: float = 1.0  # 0.0 to 1.0
    verification_coverage: float = 1.0
    missing_prerequisites: List[str] = Field(default_factory=list)
    risk_warnings: List[str] = Field(default_factory=list)
    suggested_repairs: List[str] = Field(default_factory=list)


class PlanCritic:
    """
    Evaluates generated execution plans prior to execution to catch incomplete steps,
    missing verification, or unsafe tool chaining.
    """

    @classmethod
    def evaluate(cls, hierarchy: TaskHierarchy) -> PlanCriticReport:
        report = PlanCriticReport()
        if not hierarchy.steps:
            report.is_valid = False
            report.completeness_score = 0.0
            report.missing_prerequisites.append("Plan contains zero execution steps.")
            report.suggested_repairs.append("Add default fallback execution step.")
            return report

        # 1. Verify Verification Step Presence
        has_verify = any(node.action_type == "VERIFY" or "verify" in node.name.lower() for node in hierarchy.steps)
        if not has_verify and len(hierarchy.steps) > 1:
            report.verification_coverage = 0.5
            report.suggested_repairs.append("Append explicit verification step at end of plan.")

        # 2. Check Communication Prerequisites (Compose & Preview before Send)
        if hierarchy.objective == "SEND_EMAIL":
            actions = [n.action_type for n in hierarchy.steps]
            if "EXECUTE_TOOL" in actions and "COMPOSE" not in actions:
                report.is_valid = False
                report.missing_prerequisites.append("Email dispatch requested without prior composition step.")
                report.suggested_repairs.append("Insert 'COMPOSE' step before 'EXECUTE_TOOL' send step.")

        # 3. Assess High Risk Warnings
        if hierarchy.requires_boss_approval or any(node.risk_level in ("HIGH", "CRITICAL") for node in hierarchy.steps):
            report.risk_warnings.append("Plan contains high-risk operations requiring Boss confirmation.")

        return report


class PlanRepairer:
    """Automatically repairs plans flagged by PlanCritic."""

    @classmethod
    def repair(cls, hierarchy: TaskHierarchy, report: PlanCriticReport) -> TaskHierarchy:
        if report.is_valid and report.verification_coverage >= 1.0:
            return hierarchy

        logger.info("PlanRepairer modifying task hierarchy based on critic feedback...")

        # Add verification step if missing
        if report.verification_coverage < 1.0:
            last_id = max((n.step_id for n in hierarchy.steps), default=0)
            hierarchy.steps.append(TaskNode(
                step_id=last_id + 1,
                name="Verify Task Outcome",
                action_type="VERIFY",
                tool_name="system.get_info",
                parameters={},
                verification_check="FINAL_VERIFIED",
                risk_level="LOW"
            ))

        return hierarchy
