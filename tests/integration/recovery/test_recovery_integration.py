"""
Integration test suite for JarvisRecoveryManager across simulated failure scenarios.
"""

import pytest
from jarvis.core.recovery.errors import HumanInterventionRequiredError, RecoveryLoopDetectedError
from jarvis.core.recovery.failure import FailureCategory
from jarvis.core.recovery.recovery import JarvisRecoveryManager
from jarvis.core.recovery.root_cause import ConfidenceLevel
from jarvis.core.recovery.strategies import RecoveryStrategyType


def test_scenario_1_safe_retry_recovery():
    mgr = JarvisRecoveryManager()
    can_rec, plan, rc = mgr.handle_failure(
        execution_id="exec_test_1",
        step_id="step_app_launch",
        tool_name="application.launch",
        arguments={"name": "notepad"},
        error_message="Page navigation timed out",
    )
    assert can_rec is True
    assert plan is not None
    assert plan.strategy == RecoveryStrategyType.RETRY_ONCE


def test_scenario_2_stale_visual_target_recovery():
    mgr = JarvisRecoveryManager()
    can_rec, plan, rc = mgr.handle_failure(
        execution_id="exec_test_2",
        step_id="step_click_settings",
        tool_name="screen.find",
        arguments={"target": "Settings"},
        error_message="Visual target not found on screen",
    )
    assert can_rec is True
    assert plan is not None
    assert plan.strategy == RecoveryStrategyType.REFRESH_STATE


def test_scenario_3_file_missing_recovery():
    mgr = JarvisRecoveryManager()
    can_rec, plan, rc = mgr.handle_failure(
        execution_id="exec_test_3",
        step_id="step_read_doc",
        tool_name="filesystem.read",
        arguments={"path": "C:\\nonexistent\\report.pdf"},
        error_message="No such file or directory: report.pdf",
    )
    assert can_rec is True
    assert plan is not None
    assert plan.strategy == RecoveryStrategyType.REQUERY_FILESYSTEM


def test_scenario_4_high_risk_human_intervention():
    mgr = JarvisRecoveryManager()
    with pytest.raises(HumanInterventionRequiredError) as exc_info:
        mgr.handle_failure(
            execution_id="exec_test_4",
            step_id="step_dangerous_action",
            tool_name="shell.execute",
            arguments={"command": "format C:"},
            error_message="Permission denied by security policy",
        )
    reason_str = str(exc_info.value.reason).lower()
    assert "security policy" in reason_str or "human intervention" in reason_str or "high risk" in reason_str


def test_scenario_5_loop_detection():
    mgr = JarvisRecoveryManager()
    # Call identical failure 3 times
    for i in range(2):
        mgr.handle_failure(
            execution_id="exec_test_5",
            step_id="step_loop",
            tool_name="browser.navigate",
            arguments={"url": "http://broken.local"},
            error_message="Connection refused",
        )

    with pytest.raises(RecoveryLoopDetectedError):
        mgr.handle_failure(
            execution_id="exec_test_5",
            step_id="step_loop",
            tool_name="browser.navigate",
            arguments={"url": "http://broken.local"},
            error_message="Connection refused",
        )
