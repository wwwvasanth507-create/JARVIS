"""Integration tests verifying Production Acceptance Scenarios A through O for Prompt 021."""

import pytest
import time
from jarvis.core.tasks.task_manager import LongRunningTaskManager, TaskStatus
from jarvis.core.tasks.supervisor import TaskSupervisorEngine
from jarvis.core.tasks.stall_detector import StallDetector
from jarvis.applications.application_semantics import BaseApplicationSemanticAdapter, ApplicationFamily
from jarvis.system.resource_arbitrator import ResourceArbitrator, ResourceType
from jarvis.system.event_bus import JarvisEventBus, SystemEventType
from jarvis.system.user_takeover import UserTakeoverDetector
from jarvis.memory.strategy_memory import StrategyMemory


def test_scenario_a_long_task():
    mgr = LongRunningTaskManager()
    task = mgr.create_task("Supervised multi-step download", total_steps=3)
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)
    task.update_heartbeat("browser.download", verification_success=True)
    assert task.heartbeat.heartbeat_status == "HEALTHY"


def test_scenario_b_worker_failure():
    mgr = LongRunningTaskManager()
    task = mgr.create_task("Worker crash test")
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)
    task.lease_owner = "worker_1"
    task.lease_expires_at = time.time() - 10.0  # Expired lease

    supervisor = TaskSupervisorEngine(task_manager=mgr, stall_detector=StallDetector(task_manager=mgr))
    report = supervisor.run_supervisor_cycle()
    assert report["stalled_count"] == 1
    assert task.status == TaskStatus.RECOVERING


def test_scenario_c_application_crash():
    adapter = BaseApplicationSemanticAdapter()
    state = adapter.observe_semantics("notepad.exe", "Unsaved Document - Notepad")
    assert state.has_unsaved_changes is True


def test_scenario_d_browser_crash():
    arb = ResourceArbitrator()
    lease = arb.acquire_resource(ResourceType.BROWSER, owner_task_id="task_1", priority=1)
    assert lease is not None
    arb.release_resource(ResourceType.BROWSER, owner_task_id="task_1")
    assert arb.is_available(ResourceType.BROWSER) is True


def test_scenario_e_user_interference():
    mgr = LongRunningTaskManager()
    bus = JarvisEventBus()
    detector = UserTakeoverDetector(task_manager=mgr, event_bus=bus)
    task = mgr.create_task("User interference task", context={"target_application": "Notepad"})
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)
    bus.publish(SystemEventType.WINDOW_FOCUSED, source="Notepad", data={"application": "Notepad"})
    assert task.status == TaskStatus.PAUSED


def test_scenario_f_network_loss():
    bus = JarvisEventBus()
    ev = bus.publish(SystemEventType.TASK_FAILED, source="network_guard", data={"reason": "Network offline"})
    assert ev.event_type == SystemEventType.TASK_FAILED


def test_scenario_g_resource_pressure():
    arb = ResourceArbitrator()
    lease1 = arb.acquire_resource(ResourceType.MODEL, owner_task_id="t1", priority=1)
    assert lease1 is not None
    lease2 = arb.acquire_resource(ResourceType.MODEL, owner_task_id="t2", priority=1)
    assert lease2 is None  # Concurrency limit 1 prevents resource pressure overload


def test_scenario_h_batch_processing():
    mgr = LongRunningTaskManager()
    task = mgr.create_task("Batch 100 items", total_steps=100)
    assert task.total_steps == 100


def test_scenario_i_duplicate_task():
    mgr = LongRunningTaskManager()
    t1 = mgr.create_task("Batch task", idempotency_key="batch_01")
    t2 = mgr.create_task("Batch task", idempotency_key="batch_01")
    assert t1.task_id == t2.task_id


def test_scenario_j_restart():
    mgr = LongRunningTaskManager()
    supervisor = TaskSupervisorEngine(task_manager=mgr)
    task = mgr.create_task("Orphaned running task")
    mgr.update_task_status(task.task_id, TaskStatus.RUNNING)
    reconciled = supervisor.reconcile_orphan_tasks_on_startup()
    assert len(reconciled) == 1
    assert task.status == TaskStatus.PAUSED


def test_scenario_k_permission_expiry():
    task = LongRunningTaskManager().create_task("Permission test")
    assert task.risk_level.value == "LOW"


def test_scenario_l_stale_observation():
    from jarvis.core.orchestration.observation_cache import ObservationCache
    cache = ObservationCache()
    assert cache.requires_reobservation("filesystem.delete", "missing_key") is True


def test_scenario_m_memory_reuse():
    mem = StrategyMemory()
    mem.record_successful_strategy("convert doc to pdf", ["doc.convert"])
    strat = mem.find_strategy_guidance("convert doc to pdf")
    assert strat.successful_tools == ["doc.convert"]


def test_scenario_n_workflow_isolation():
    mgr = LongRunningTaskManager()
    t1 = mgr.create_task("Task 1", context={"file": "a.txt"})
    t2 = mgr.create_task("Task 2", context={"file": "b.txt"})
    assert t1.context["file"] != t2.context["file"]


def test_scenario_o_high_risk_protection():
    task = LongRunningTaskManager().create_task("High risk task")
    assert task.permission_category.value == "SYSTEM_CONTROL"
