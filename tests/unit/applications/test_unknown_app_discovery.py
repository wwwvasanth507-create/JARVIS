"""
Unit tests for Unknown Application Discovery Engine.
"""

import pytest
from jarvis.applications.unknown_app_discovery import UnknownApplicationDiscovery, DiscoveredAppProfile, DiscoveredControl


def test_01_unknown_app_discovery_instantiation():
    disc = UnknownApplicationDiscovery.get_instance()
    profile = disc.inspect_active_application()
    
    if profile is not None:
        assert isinstance(profile, DiscoveredAppProfile)
        assert profile.process_name != ""
        assert profile.category in ("TEXT_EDITOR", "BROWSER", "DOCUMENT_VIEWER", "COMMUNICATION", "GENERIC_DESKTOP_APP")


def test_02_find_control_by_label():
    disc = UnknownApplicationDiscovery.get_instance()
    profile = DiscoveredAppProfile(
        process_name="test_app.exe",
        window_title="Test Application",
        hwnd=12345,
        category="UTILITY",
        discovered_controls=[
            DiscoveredControl(control_id="c1", control_type="BUTTON", label="Submit Request"),
            DiscoveredControl(control_id="c2", control_type="TEXTBOX", label="User Address"),
        ]
    )

    ctrl = disc.find_control_by_label(profile, "Submit")
    assert ctrl is not None
    assert ctrl.control_id == "c1"

    ctrl_none = disc.find_control_by_label(profile, "Nonexistent")
    assert ctrl_none is None
