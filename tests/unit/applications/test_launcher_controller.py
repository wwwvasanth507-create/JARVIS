"""
Unit tests for application launcher, graceful close, readiness, and health checks.
"""

import pytest
from jarvis.applications.state import ApplicationInfo
from jarvis.applications.launcher import ApplicationLauncher
from jarvis.applications.controller import ApplicationController


def test_url_association_launcher():
    launcher = ApplicationLauncher()
    res = launcher.open_url("https://example.com")
    assert res.success
    assert res.verified


def test_invalid_url_scheme_rejection():
    launcher = ApplicationLauncher()
    with pytest.raises(ValueError):
        launcher.open_url("ftp://example.com")


def test_health_check_non_running():
    controller = ApplicationController()
    app = ApplicationInfo(name="FakeApp", executable="fake_app_99.exe")

    health = controller.check_health(app)
    assert not health.running
    assert health.status == "stopped"
