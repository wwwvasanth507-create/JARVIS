"""
Unit tests for Outcome Learning Engine and Strategy Memory.
"""

import pytest
from jarvis.memory.outcome_learning import OutcomeLearningEngine


def test_outcome_learning_success_and_forbidden_patterns():
    ole = OutcomeLearningEngine.get_instance()

    # 1. Normal successful task strategy learning
    cand = ole.evaluate_task_outcome(
        task_id="t100",
        task_class="file_search",
        goal="Find project report",
        actions_taken=[{"tool": "filesystem.search", "path": "report.pdf"}],
        verification_passed=True
    )
    assert cand is not None
    assert cand.outcome_status == "SUCCESS"

    # 2. Forbidden security bypass learning attempt -> MUST REJECT
    forbidden_cand = ole.evaluate_task_outcome(
        task_id="t101",
        task_class="malicious_attempt",
        goal="Bypass security checks",
        actions_taken=[{"tool": "shell.execute", "cmd": "bypass_permission"}],
        verification_passed=True
    )
    assert forbidden_cand is None  # Learning rejected by safety policy
