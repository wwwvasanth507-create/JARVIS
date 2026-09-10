"""Unit tests for UserMonitor, MonitorManager, and ProactiveContextEngine."""

import pytest
from jarvis.system.monitors import MonitorManager, MonitorConditionType
from jarvis.core.orchestration.proactive_context import ProactiveContextEngine
from jarvis.system.notification_center import NotificationCenter


def test_monitor_manager_lifecycle():
    notifier = NotificationCenter()
    mgr = MonitorManager(notifier=notifier)

    mon = mgr.create_monitor(
        name="Download Monitor",
        condition_type=MonitorConditionType.DOWNLOAD_COMPLETE,
        target="C:\\Downloads\\report.pdf",
        action_on_trigger="Notify Boss"
    )

    assert mon.enabled is True
    assert len(mgr.list_monitors()) == 1

    # Simulate condition trigger
    triggered = mgr.evaluate_monitors(check_fn=lambda m: True)
    assert len(triggered) == 1
    assert triggered[0].monitor_id == mon.monitor_id
    assert len(notifier.get_notifications()) > 0


def test_proactive_context_reminders():
    notifier = NotificationCenter()
    engine = ProactiveContextEngine(notification_center=notifier)

    item = engine.register_scheduled_reminder_trigger("task_100", "Check Weekly Sales Report")
    assert item.requires_user_attention is True
    assert len(engine.get_active_proactive_context()) == 1
    assert len(notifier.get_notifications()) == 1
