"""
Unit tests for protected application safety checks and unsaved-work detection.
"""

import pytest
from jarvis.applications.safety import ApplicationSafety
from jarvis.applications.state import ApplicationInfo
from jarvis.applications.errors import ProtectedApplicationBlocked


def test_protected_security_application_safety():
    safety = ApplicationSafety()
    protected_app = ApplicationInfo(name="Windows Defender", executable="MsMpEng.exe")

    assert safety.is_protected(protected_app)

    with pytest.raises(ProtectedApplicationBlocked):
        safety.check_safety(protected_app, operation="close")


def test_unsaved_work_detection():
    safety = ApplicationSafety()
    editor_app = ApplicationInfo(name="Visual Studio Code", executable="Code.exe")
    calc_app = ApplicationInfo(name="Calculator", executable="calc.exe")

    assert safety.detect_unsaved_work(editor_app)
    assert not safety.detect_unsaved_work(calc_app)
