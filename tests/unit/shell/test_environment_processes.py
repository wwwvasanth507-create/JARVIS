"""
Unit tests for secret environment redaction and process inspection.
"""

import os
import pytest
from jarvis.shell.environment import ShellEnvironment
from jarvis.shell.processes import ProcessManager


def test_environment_secret_redaction(monkeypatch):
    monkeypatch.setenv("MY_APP_PASSWORD", "supersecret123")
    monkeypatch.setenv("API_TOKEN", "bearer_token_xyz")
    monkeypatch.setenv("NORMAL_VAR", "hello_world")

    shell_env = ShellEnvironment()
    sanitized = shell_env.get_sanitized_environment()

    assert sanitized["MY_APP_PASSWORD"] == "[REDACTED]"
    assert sanitized["API_TOKEN"] == "[REDACTED]"
    assert sanitized["NORMAL_VAR"] == "hello_world"


def test_process_manager_listing():
    pm = ProcessManager()
    procs = pm.list_processes(limit=10)

    assert len(procs) > 0
    current_pid = os.getpid()
    self_proc = pm.get_process(current_pid)
    assert self_proc.pid == current_pid
    assert self_proc.name != ""
