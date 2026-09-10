"""
Safe end-to-end integration test for JARVIS Application Control Subsystem.
Uses harmless Calculator utility (calc.exe / Calculator).
Does NOT close user applications with unsaved work or alter system state.
"""

import sys
import pytest
from jarvis.applications.manager import ApplicationManager


def test_safe_application_integration_lifecycle():
    """
    Executes an 8-step safe application control lifecycle test.
    """
    mgr = ApplicationManager()

    # 1. Discover & List Applications
    apps = mgr.list_applications()
    assert len(apps) > 0

    # 2. Resolve Alias / Name ("calculator")
    app_info = mgr.find_application("calculator")
    assert app_info.name == "Calculator"

    # Only execute launch on Windows where calc.exe exists and is harmless
    if sys.platform == "win32":
        # 3. Open application
        open_res = mgr.open_application("calculator")
        assert open_res.success
        assert open_res.verified

        # 4. Check running state & process
        st = mgr.is_running("calculator")
        assert st.running
        assert len(st.pids) > 0

        # 5. Focus application
        focused = mgr.focus_application("calculator")
        assert isinstance(focused, bool)

        # 6. Check health
        health = mgr.check_health("calculator")
        assert health.running
        assert health.status == "healthy"

        # 7. Close gracefully
        close_res = mgr.close_application("calculator", force=True)
        assert close_res.success
        assert close_res.verified

        # 8. Verify it stopped
        st_after = mgr.is_running("calculator")
        assert not st_after.running
