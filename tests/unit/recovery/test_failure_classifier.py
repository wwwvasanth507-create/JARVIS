"""
Unit tests for FailureClassifier.
"""

from jarvis.core.recovery.classifier import FailureClassifier
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.root_cause import ConfidenceLevel


def test_classify_permission_denied():
    classifier = FailureClassifier()
    event = FailureEvent(
        execution_id="exec_1",
        step_id="step_1",
        tool_name="shell.execute",
        error_message="Permission denied by security policy",
    )
    rc = classifier.classify(event)
    assert rc.category == FailureCategory.PERMISSION_DENIED
    assert rc.confidence == ConfidenceLevel.LIKELY


def test_classify_timeout():
    classifier = FailureClassifier()
    event = FailureEvent(
        execution_id="exec_1",
        step_id="step_1",
        tool_name="browser.navigate",
        error_message="Page navigation timed out",
    )
    rc = classifier.classify(event)
    assert rc.category == FailureCategory.TIMEOUT
    assert rc.confidence == ConfidenceLevel.LIKELY


def test_classify_path_invalid():
    classifier = FailureClassifier()
    event = FailureEvent(
        execution_id="exec_1",
        step_id="step_1",
        tool_name="filesystem.read",
        error_message="No such file or directory: /tmp/missing.txt",
    )
    rc = classifier.classify(event)
    assert rc.category == FailureCategory.PATH_INVALID
    assert rc.confidence == ConfidenceLevel.LIKELY
