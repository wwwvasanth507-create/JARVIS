"""
Unit tests for Application Lifecycle Manager and JARVIS Bootstrap.
"""

import pytest
from jarvis.core.lifecycle import (
    LifecycleManager,
    ApplicationState,
    InvalidStateTransitionError
)
from jarvis.app import JARVISApp


def test_lifecycle_initial_state():
    mgr = LifecycleManager()
    assert mgr.state == ApplicationState.CREATED
    assert not mgr.is_running()
    assert not mgr.is_ready()
    assert not mgr.is_stopped()


def test_lifecycle_allowed_transitions():
    mgr = LifecycleManager()
    assert mgr.transition_to(ApplicationState.VALIDATING)
    assert mgr.state == ApplicationState.VALIDATING
    assert mgr.transition_to(ApplicationState.INITIALIZING)
    assert mgr.transition_to(ApplicationState.READY)
    assert mgr.is_ready()
    assert mgr.transition_to(ApplicationState.RUNNING)
    assert mgr.is_running()
    assert mgr.transition_to(ApplicationState.READY)
    assert mgr.transition_to(ApplicationState.STOPPING)
    assert mgr.transition_to(ApplicationState.STOPPED)
    assert mgr.is_stopped()


def test_lifecycle_invalid_transition_raises_error():
    mgr = LifecycleManager()
    with pytest.raises(InvalidStateTransitionError):
        mgr.transition_to(ApplicationState.RUNNING)


def test_lifecycle_idempotent_transition():
    mgr = LifecycleManager()
    mgr.transition_to(ApplicationState.VALIDATING)
    # Re-transitioning to same state should return True without error
    assert mgr.transition_to(ApplicationState.VALIDATING)


def test_app_bootstrap_safe_mode():
    app = JARVISApp(safe_mode=True)
    assert app.initialize()
    assert app.lifecycle.is_ready()
    
    # Fast path check
    res = app.execute_command("what time is it")
    assert res["success"] is True
    assert "current time" in res["response"].lower()
    assert res["fast_path"] is True

    # System status fast path check
    status_res = app.execute_command("system status")
    assert status_res["success"] is True
    assert status_res["data"]["safe_mode"] is True

    app.shutdown()
    assert app.lifecycle.is_stopped()
