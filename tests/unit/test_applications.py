"""
Unit tests for ApplicationRegistry, ApplicationDetector, and ApplicationLauncher.
"""

import pytest
from jarvis.applications.registry import ApplicationRegistry
from jarvis.applications.detector import ApplicationDetector
from jarvis.applications.launcher import ApplicationLauncher


def test_application_registry_resolution():
    reg = ApplicationRegistry()
    
    # Resolve chrome alias
    entry_chrome = reg.resolve("chrome")
    assert entry_chrome is not None
    assert entry_chrome.executable == "chrome.exe"

    # Resolve notepad alias
    entry_notepad = reg.resolve("notepad")
    assert entry_notepad is not None
    assert entry_notepad.executable == "notepad.exe"

    # Resolve calculator alias
    entry_calc = reg.resolve("calculator")
    assert entry_calc is not None
    assert entry_calc.executable == "calc.exe"


def test_application_detector_process_check():
    reg = ApplicationRegistry()
    entry_calc = reg.resolve("calc")
    status = ApplicationDetector.get_status(entry_calc)

    assert status.name == entry_calc.name
    assert status.executable == entry_calc.executable
    assert isinstance(status.is_running, bool)
