"""
Safe end-to-end integration test for JARVIS Controlled Shell Subsystem.
Uses exclusively harmless commands (python --version, git --version, echo test).
Does NOT alter or mutate system state.
"""

import pytest
from pathlib import Path
from jarvis.shell.manager import ShellManager


def test_safe_shell_integration_lifecycle(tmp_path):
    """
    Executes a 6-step safe integration lifecycle test for shell tools.
    """
    mgr = ShellManager()
    mgr.permission_checker.validator.path_resolver.allowed_roots = [tmp_path.resolve(strict=False)]

    # 1. Command Accepted & Permission Checked (python --version)
    res_py = mgr.execute("python --version", working_directory=tmp_path)
    assert res_py.exit_code == 0
    assert "Python" in (res_py.stdout + res_py.stderr)

    # 2. Execute git --version or echo test
    res_echo = mgr.execute("echo 'JARVIS Shell Integration Test'", working_directory=tmp_path)
    assert res_echo.exit_code == 0
    assert "JARVIS Shell Integration Test" in res_echo.stdout

    # 3. Output Captured & Verified
    assert res_echo.verified

    # 4. Environment & Process Metadata Inspection
    env_data = mgr.get_environment()
    assert isinstance(env_data, dict)

    procs = mgr.list_processes(limit=5)
    assert len(procs) > 0

    # 5. Audit Event Recorded
    assert len(mgr.audit_log) >= 2
    audit_rec = mgr.audit_log[-1]
    assert audit_rec.status == "completed"
    assert audit_rec.permission_allowed
