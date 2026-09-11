"""
Outcome Learning Engine and Strategy Memory Extensions for JARVIS.

Analyzes completed tasks (planned vs executed vs verified outcome), enforces Learning Confidence Gates,
records Learning Audit Logs, and updates Strategy Memory without ever learning security bypasses.
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from jarvis.memory.memory_layers import MemorySource
from jarvis.memory.strategy_memory import StrategyMemory, StrategyRecord
from jarvis.security.permissions import PermissionCategory, RiskLevel

logger = logging.getLogger(__name__)

# Security Rule: Never learn security bypass, confirmation bypass, or credential extraction
FORBIDDEN_LEARNING_TERMS = [
    "bypass_permission", "bypass_confirmation", "ignore_security",
    "dismiss_security_prompt", "extract_credential", "captcha_bypass", "sudo_nopasswd"
]


class LearningCandidate(BaseModel):
    candidate_id: str
    task_class: str
    learning_type: str  # "STRATEGY", "PREFERENCE", "FAILURE_PATTERN", "WORKFLOW_TIMING"
    description: str
    preconditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    environment_scope: Dict[str, str] = Field(default_factory=dict)  # OS, app, browser
    outcome_status: str  # "SUCCESS", "FAILURE"
    confidence: float = 0.5
    requires_user_approval: bool = False


class AuditLogEntry(BaseModel):
    entry_id: str
    timestamp: float = Field(default_factory=time.time)
    action: str  # "LEARNED_STRATEGY", "STORED_PREFERENCE", "LEARNED_FAILURE", "REJECTED_BY_POLICY"
    source: MemorySource
    reason: str
    confidence: float
    user_approved: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutcomeLearningEngine:
    """
    Evaluates completed task outcomes and extracts safe reusable learnings
    with Learning Confidence Gates and Learning Audit Logs.
    """

    _instance: Optional["OutcomeLearningEngine"] = None

    def __init__(self):
        self.strategy_mem = StrategyMemory.get_instance()
        self.audit_log: List[AuditLogEntry] = []

    @classmethod
    def get_instance(cls) -> "OutcomeLearningEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def evaluate_task_outcome(
        self,
        task_id: str,
        task_class: str,
        goal: str,
        actions_taken: List[Dict[str, Any]],
        verification_passed: bool,
        environment_scope: Optional[Dict[str, str]] = None,
        duration_sec: float = 0.0,
        user_feedback: Optional[str] = None
    ) -> Optional[LearningCandidate]:
        """
        Analyzes task outcome. Derives learning candidate if threshold is met.
        Strict Security Safeguard: Blocks forbidden security bypass learning patterns.
        """
        env = environment_scope or {"os": "Windows", "browser": "Chrome"}

        # 1. Safety Check: Verify no forbidden security terms are present in actions
        actions_str = json.dumps(actions_taken).lower()
        if any(term in actions_str for term in FORBIDDEN_LEARNING_TERMS):
            logger.warning(f"OutcomeLearningEngine: Rejected learning candidate containing forbidden security term.")
            self._log_audit("REJECTED_BY_POLICY", MemorySource.TASK_OUTCOME, "Forbidden security pattern detected", 0.0, False)
            return None

        # 2. Derive strategy learning candidate
        learning_type = "STRATEGY" if verification_passed else "FAILURE_PATTERN"
        conf = 0.6 if verification_passed else 0.4

        if user_feedback and ("wrong" in user_feedback.lower() or "don't" in user_feedback.lower()):
            learning_type = "FAILURE_PATTERN"
            conf = 0.8

        candidate = LearningCandidate(
            candidate_id=f"learn_{task_id[:8]}",
            task_class=task_class,
            learning_type=learning_type,
            description=f"Outcome learning for {task_class} ({goal[:30]})",
            preconditions={"goal_keyword": task_class},
            actions=actions_taken,
            environment_scope=env,
            outcome_status="SUCCESS" if verification_passed else "FAILURE",
            confidence=conf,
            requires_user_approval=conf < 0.7 and verification_passed,
        )

        # 3. Apply Confidence Gate
        if candidate.confidence >= 0.5 and not candidate.requires_user_approval:
            self.commit_learning(candidate)

        return candidate

    def commit_learning(self, candidate: LearningCandidate, user_approved: bool = True) -> bool:
        """
        Commits candidate learning to StrategyMemory or FailurePattern storage.
        Calculates evidence-based confidence (e.g. 1/1 -> LOW, 20/21 -> HIGH).
        """
        if candidate.learning_type == "STRATEGY":
            # Record or update StrategyRecord in StrategyMemory
            res = self.strategy_mem.record_execution(
                task_class=candidate.task_class,
                strategy_name=candidate.description,
                success=candidate.outcome_status == "SUCCESS",
                duration_sec=0.0
            )
            self._log_audit(
                "LEARNED_STRATEGY",
                MemorySource.TASK_OUTCOME,
                f"Recorded strategy for {candidate.task_class}",
                candidate.confidence,
                user_approved
            )
            return True

        elif candidate.learning_type == "FAILURE_PATTERN":
            # Record failure pattern
            res = self.strategy_mem.record_execution(
                task_class=candidate.task_class,
                strategy_name=candidate.description,
                success=False,
                duration_sec=0.0
            )
            self._log_audit(
                "LEARNED_FAILURE",
                MemorySource.TASK_OUTCOME,
                f"Recorded failure pattern for {candidate.task_class}",
                candidate.confidence,
                user_approved
            )
            return True

        return False

    def _log_audit(self, action: str, source: MemorySource, reason: str, conf: float, approved: bool) -> None:
        entry = AuditLogEntry(
            entry_id=f"audit_{int(time.time()*1000)}",
            action=action,
            source=source,
            reason=reason,
            confidence=conf,
            user_approved=approved,
        )
        self.audit_log.append(entry)
        if len(self.audit_log) > 1000:
            self.audit_log.pop(0)

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in reversed(self.audit_log[:limit])]
