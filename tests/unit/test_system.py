"""
Unit tests for JARVIS System, Hardware Detection, Resource Management, Task Queue, and Fast Intent Router.
"""

from jarvis.system.hardware import HardwareDetector, HardwareProfile, HardwareProfileTier
from jarvis.system.resource_manager import ResourceManager
from jarvis.system.task_queue import TaskQueue, TaskPriority, TaskStatus
from jarvis.brain.fast_path import FastIntentRouter


def test_hardware_detection():
    profile = HardwareDetector.detect()
    assert isinstance(profile, HardwareProfile)
    assert profile.physical_cores >= 1
    assert profile.logical_cores >= 1
    assert profile.ram_gb > 0.0
    assert profile.profile_tier in HardwareProfileTier


def test_hardware_tier_classification():
    # Test ULTRA_LOW
    t1 = HardwareDetector._classify_tier(ram_gb=4.0, physical_cores=2, gpu_available=False, vram_gb=0.0)
    assert t1 == HardwareProfileTier.ULTRA_LOW

    # Test LOW
    t2 = HardwareDetector._classify_tier(ram_gb=8.0, physical_cores=4, gpu_available=False, vram_gb=0.0)
    assert t2 == HardwareProfileTier.LOW

    # Test GPU_ACCELERATED
    t3 = HardwareDetector._classify_tier(ram_gb=16.0, physical_cores=8, gpu_available=True, vram_gb=8.0)
    assert t3 == HardwareProfileTier.GPU_ACCELERATED


def test_resource_manager():
    rm = ResourceManager(high_cpu_threshold=85.0, high_ram_threshold=90.0)
    status = rm.get_status(active_task_count=1)
    assert status.ram_total_gb > 0.0
    assert isinstance(status.background_indexing_paused, bool)


def test_task_queue_prioritization():
    queue = TaskQueue()
    t_low = queue.enqueue("low_task", priority=TaskPriority.LOW)
    t_high = queue.enqueue("high_task", priority=TaskPriority.HIGH)
    t_crit = queue.enqueue("crit_task", priority=TaskPriority.CRITICAL)

    # Highest priority should pop first
    popped1 = queue.pop_next()
    assert popped1.id == t_crit.id
    assert popped1.status == TaskStatus.RUNNING

    popped2 = queue.pop_next()
    assert popped2.id == t_high.id

    popped3 = queue.pop_next()
    assert popped3.id == t_low.id

    # Queue should be empty now
    assert queue.pop_next() is None


def test_fast_intent_router():
    # Match deterministic commands
    res1 = FastIntentRouter.match("Open Chrome")
    assert res1.matched is True
    assert res1.target_tool == "application.open"
    assert res1.fast_response == "Opening Chrome, Boss."

    res2 = FastIntentRouter.match("Take a screenshot")
    assert res2.matched is True
    assert res2.target_tool == "computer.screenshot"

    res3 = FastIntentRouter.match("Pause music")
    assert res3.matched is True
    assert res3.target_tool == "computer.key_press"

    # Non-matched complex command should fall through
    res_complex = FastIntentRouter.match("Reorganize my documents folder into categories")
    assert res_complex.matched is False
