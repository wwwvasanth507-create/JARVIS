"""
JARVIS Recovery & Diagnostic Subsystem.
"""

from jarvis.core.recovery.errors import (
    RecoveryError,
    RecoveryLimitExceededError,
    RecoveryLoopDetectedError,
    HumanInterventionRequiredError,
    DiagnosticFailedError,
    RecoveryPermissionDeniedError,
)
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause
from jarvis.core.recovery.evidence import DiagnosticEvidence, EvidenceCollector
from jarvis.core.recovery.classifier import FailureClassifier
from jarvis.core.recovery.diagnostics import DiagnosticEngine
from jarvis.core.recovery.strategies import RecoveryStrategy, RecoveryStrategyType, StrategyRegistry
from jarvis.core.recovery.planner import RecoveryPlanner, RecoveryPlan, RecoveryStep
from jarvis.core.recovery.limits import RecoveryLimits
from jarvis.core.recovery.state import RecoveryState, RecoveryStatus
from jarvis.core.recovery.policy import RecoveryPolicy
from jarvis.core.recovery.replanner import DiagnosticReplanner
from jarvis.core.recovery.executor import RecoveryExecutor
from jarvis.core.recovery.recovery import JarvisRecoveryManager

__all__ = [
    "RecoveryError",
    "RecoveryLimitExceededError",
    "RecoveryLoopDetectedError",
    "HumanInterventionRequiredError",
    "DiagnosticFailedError",
    "RecoveryPermissionDeniedError",
    "FailureCategory",
    "FailureEvent",
    "ConfidenceLevel",
    "RootCause",
    "DiagnosticEvidence",
    "EvidenceCollector",
    "FailureClassifier",
    "DiagnosticEngine",
    "RecoveryStrategy",
    "RecoveryStrategyType",
    "StrategyRegistry",
    "RecoveryPlanner",
    "RecoveryPlan",
    "RecoveryStep",
    "RecoveryLimits",
    "RecoveryState",
    "RecoveryStatus",
    "RecoveryPolicy",
    "DiagnosticReplanner",
    "RecoveryExecutor",
    "JarvisRecoveryManager",
]
