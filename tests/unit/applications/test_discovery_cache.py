"""
Unit tests for OS-native application discovery and index cache.
"""

import pytest
from pathlib import Path
from jarvis.applications.discovery import ApplicationDiscovery, ApplicationCache
from jarvis.applications.state import ApplicationInfo


def test_discovery_and_cache(tmp_path):
    cache_file = tmp_path / "applications.json"
    discovery = ApplicationDiscovery(cache_file=cache_file)

    apps = [
        ApplicationInfo(name="Notepad", executable="notepad.exe", common_paths=["C:\\Windows\\System32\\notepad.exe"])
    ]

    discovered = discovery.discover_applications(apps)
    assert cache_file.exists()

    loaded = discovery.load_cache()
    assert loaded is not None
    assert loaded.discovered_count == len(discovered)
