"""
Unit tests for JARVIS CLI entrypoint parsing and commands.
"""

import sys
import pytest
from unittest.mock import patch
from jarvis.__main__ import main


def test_cli_version_flag(capsys):
    with patch.object(sys, "argv", ["jarvis", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "JARVIS Personal Desktop Assistant v0.1.0" in captured.out


def test_cli_self_test_flag(capsys):
    with patch.object(sys, "argv", ["jarvis", "--self-test"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "JARVIS SELF-TEST SUITE" in captured.out
    assert "Overall Self-Test Result: PASS" in captured.out


def test_cli_doctor_flag(capsys):
    with patch.object(sys, "argv", ["jarvis", "--doctor"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "JARVIS DOCTOR DIAGNOSTICS" in captured.out


def test_cli_release_check_flag(capsys):
    with patch.object(sys, "argv", ["jarvis", "--release-check"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "JARVIS PRODUCTION RELEASE CHECK" in captured.out
    assert "FINAL RELEASE DECISION: RELEASE READY" in captured.out
