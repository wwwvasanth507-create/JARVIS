"""
Unit tests for DiagnosticEngine.
"""

from jarvis.core.recovery.diagnostics import DiagnosticEngine
from jarvis.core.recovery.failure import FailureCategory, FailureEvent


def test_diagnose_nonexistent_path():
    engine = DiagnosticEngine()
    event = FailureEvent(
        execution_id="exec_1",
        step_id="step_1",
        tool_name="filesystem.read",
        arguments_summary={"path": "C:\\nonexistent_folder_xyz123\\file.txt"},
        error_message="File not found",
    )
    rc, evidence = engine.diagnose(event)
    assert rc.category == FailureCategory.PATH_INVALID
    assert evidence.filesystem_state is not None
    assert evidence.filesystem_state.get("exists") is False


def test_diagnose_resource_state():
    engine = DiagnosticEngine()
    event = FailureEvent(
        execution_id="exec_1",
        step_id="step_1",
        tool_name="shell.execute",
        error_message="Unknown command error",
    )
    rc, evidence = engine.diagnose(event)
    assert evidence.resource_state is not None
    assert "ram_available_mb" in evidence.resource_state
