"""
Unit tests for synchronous execution, output truncation, timeouts, background jobs, and cancellation.
"""

import time
import pytest
from pathlib import Path
from jarvis.shell.parser import CommandParser
from jarvis.shell.executor import ShellExecutor


def test_sync_execution_and_output_truncation(tmp_path):
    executor = ShellExecutor(max_stdout_bytes=50)
    parsed = CommandParser.parse("python -c \"print('A' * 200)\"")

    res = executor.execute_sync(parsed, working_directory=tmp_path, timeout=10)
    assert res.exit_code == 0
    assert res.truncated
    assert len(res.stdout) <= 50


def test_execution_timeout(tmp_path):
    executor = ShellExecutor()
    parsed = CommandParser.parse("python -c \"import time; time.sleep(5)\"")

    res = executor.execute_sync(parsed, working_directory=tmp_path, timeout=1)
    assert res.timed_out
    assert res.exit_code == -1


def test_background_job_lifecycle_and_cancellation(tmp_path):
    executor = ShellExecutor()
    parsed = CommandParser.parse("python -c \"import time; time.sleep(10)\"")

    job = executor.start_background_job(parsed, working_directory=tmp_path, timeout=30)
    assert job.status == "RUNNING"

    # Cancel job
    cancelled_job = executor.cancel_job(job.job_id)
    assert cancelled_job.status == "CANCELLED"
