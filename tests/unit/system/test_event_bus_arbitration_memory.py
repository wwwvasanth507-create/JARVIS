"""Unit tests for JarvisEventBus, ResourceArbitrator, StrategyMemory, and UserTakeoverDetector."""

import pytest
from jarvis.system.event_bus import JarvisEventBus, SystemEventType, SystemEvent
from jarvis.system.resource_arbitrator import ResourceArbitrator, ResourceType
from jarvis.memory.strategy_memory import StrategyMemory
from jarvis.system.user_takeover import UserTakeoverDetector
from jarvis.core.tasks.task_manager import LongRunningTaskManager, TaskStatus


def test_event_bus_publish_subscribe():
    bus = JarvisEventBus()
    received_events = []

    bus.subscribe(SystemEventType.TASK_COMPLETED, lambda e: received_events.append(e))
    bus.publish(SystemEventType.TASK_COMPLETED, source="orchestrator", data={"task_id": "t1"})

    assert len(received_events) == 1
    assert received_events[0].source == "orchestrator"


def test_resource_arbitrator_preemption():
    arbitrator = ResourceArbitrator()
    lease_bg = arbitrator.acquire_resource(ResourceType.MODEL, owner_task_id="task_bg", priority=1, lease_sec=60.0)
    assert lease_bg is not None

    # Higher priority interrupt task preempts background lease
    lease_user = arbitrator.acquire_resource(ResourceType.MODEL, owner_task_id="task_user", priority=3, lease_sec=60.0)
    assert lease_user is not None
    assert lease_user.owner_task_id == "task_user"


def test_strategy_memory_recording():
    mem = StrategyMemory()
    mem.record_successful_strategy("summarize PDF report", ["filesystem.search", "doc.summarize"])

    guidance = mem.find_strategy_guidance("Summarize PDF report for Boss")
    assert guidance is not None
    assert guidance.successful_tools == ["filesystem.search", "doc.summarize"]


def test_user_takeover_detector():
    task_mgr = LongRunningTaskManager()
    event_bus = JarvisEventBus()
    detector = UserTakeoverDetector(task_manager=task_mgr, event_bus=event_bus)

    task = task_mgr.create_task("Background Chrome Task", context={"target_application": "Chrome"})
    task_mgr.update_task_status(task.task_id, TaskStatus.RUNNING)

    # Publish window focus event for user manual interaction in Chrome
    event_bus.publish(SystemEventType.WINDOW_FOCUSED, source="Chrome", data={"application": "Chrome"})

    assert task.status == TaskStatus.PAUSED
    assert "Safe Handoff" in task.context.get("pause_reason", "")
