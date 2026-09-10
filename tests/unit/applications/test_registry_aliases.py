"""
Unit tests for application registry, alias resolution, and ambiguity handling.
"""

import pytest
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.aliases import AliasResolver
from jarvis.applications.errors import AmbiguousApplication, ApplicationNotFound
from jarvis.applications.state import ApplicationInfo


def test_alias_resolution_exact_and_alias():
    reg = ApplicationRegistry()

    # Exact name / alias
    app_chrome = reg.resolve("chrome")
    assert app_chrome.name == "Google Chrome"

    app_vscode = reg.resolve("code")
    assert app_vscode.name == "Visual Studio Code"

    app_calc = reg.resolve("calculator")
    assert app_calc.name == "Calculator"


def test_ambiguous_application_detection():
    # Setup test entries with ambiguous aliases
    entries = {
        "chrome": ApplicationInfo(name="Google Chrome", executable="chrome.exe", aliases=["browser"]),
        "firefox": ApplicationInfo(name="Mozilla Firefox", executable="firefox.exe", aliases=["browser"]),
    }

    with pytest.raises(AmbiguousApplication) as exc_info:
        AliasResolver.resolve("browser", entries)

    assert "matched multiple candidates" in str(exc_info.value)
    assert set(exc_info.value.candidates) == {"Google Chrome", "Mozilla Firefox"}


def test_nonexistent_application_resolution():
    reg = ApplicationRegistry()
    with pytest.raises(ApplicationNotFound):
        reg.resolve("non_existent_app_12345")
