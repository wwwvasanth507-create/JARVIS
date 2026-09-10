"""
Unit tests for ScreenPrivacyPolicy.
"""

import pytest
from jarvis.computer.vision.privacy import ScreenPrivacyPolicy
from jarvis.computer.vision.errors import ScreenPrivacyDeniedError


def test_screen_privacy_policy_blocking():
    policy = ScreenPrivacyPolicy()
    assert policy.is_window_blocked("Bitwarden - Password Manager") is True
    assert policy.is_window_blocked("Chase Online Banking") is True
    assert policy.is_window_blocked("Visual Studio Code - project.py") is False


def test_screen_privacy_policy_validation_exception():
    policy = ScreenPrivacyPolicy()
    with pytest.raises(ScreenPrivacyDeniedError):
        policy.validate_screen_capture_allowed("KeePass Password Safe")
