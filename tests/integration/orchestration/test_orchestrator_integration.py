"""
Integration tests for JarvisOrchestrator end-to-end execution.
"""

from jarvis.core.orchestration.orchestrator import JarvisOrchestrator
from jarvis.core.orchestration.state import ExecutionStatus


def test_orchestrator_fast_path_application_list():
    orchestrator = JarvisOrchestrator()
    state = orchestrator.handle("list installed applications")
    
    assert state.fast_path_used is True
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.completed_steps) == 1
    assert state.completed_steps[0].tool_name == "application.list"
    assert len(orchestrator.history) == 1


def test_orchestrator_filesystem_search():
    orchestrator = JarvisOrchestrator()
    state = orchestrator.handle("search for *.py in src")
    
    assert state.status == ExecutionStatus.COMPLETED
    assert len(state.completed_steps) == 1
    assert state.completed_steps[0].tool_name == "filesystem.search"


def test_orchestrator_high_risk_confirmation_flow():
    orchestrator = JarvisOrchestrator()
    # High risk action e.g. shell command execution
    state = orchestrator.handle("run command echo hello")
    
    # Needs confirmation because shell.execute is HIGH risk
    assert state.status == ExecutionStatus.WAITING_FOR_CONFIRMATION
    token = state.confirmation_token
    assert token is not None

    # Pass token to resume execution
    state2 = orchestrator.handle("run command echo hello", confirmation_token=token)
    assert state2.status == ExecutionStatus.COMPLETED
    assert len(state2.completed_steps) == 1


def test_orchestrator_cancellation():
    orchestrator = JarvisOrchestrator()
    state = orchestrator.handle("stop")
    assert state.status == ExecutionStatus.CANCELLED
