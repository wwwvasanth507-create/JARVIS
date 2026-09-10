"""
Unit tests for System Tray Manager.
"""

from jarvis.ui.system_tray import SystemTrayManager


def test_system_tray_manager_initialization():
    mgr = SystemTrayManager()
    init_res = mgr.initialize()
    assert isinstance(init_res, bool)
    
    mgr.show_notification("Test Title", "Test Notification Message")
    mgr.shutdown()
