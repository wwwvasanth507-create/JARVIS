"""
Unit tests for Hardware Detector and Capability Registry.
"""

from jarvis.core.hardware import HardwareDetector, PerformanceProfile, HardwareSpecs
from jarvis.core.capabilities import CapabilityRegistry, CapabilityStatus


def test_hardware_detector():
    specs = HardwareDetector.detect()
    assert isinstance(specs, HardwareSpecs)
    assert specs.cpu_count >= 1
    assert specs.total_ram_gb > 0
    assert specs.performance_profile in [
        PerformanceProfile.ULTRA_LOW,
        PerformanceProfile.LOW,
        PerformanceProfile.MEDIUM,
        PerformanceProfile.HIGH,
        PerformanceProfile.GPU_ACCELERATED,
    ]


def test_determine_profile():
    p1 = HardwareDetector.determine_profile(cpu_count=2, ram_gb=3.5, gpu_available=False)
    assert p1 == PerformanceProfile.ULTRA_LOW

    p2 = HardwareDetector.determine_profile(cpu_count=4, ram_gb=7.5, gpu_available=False)
    assert p2 == PerformanceProfile.LOW

    p3 = HardwareDetector.determine_profile(cpu_count=8, ram_gb=15.0, gpu_available=False)
    assert p3 == PerformanceProfile.MEDIUM

    p4 = HardwareDetector.determine_profile(cpu_count=16, ram_gb=32.0, gpu_available=False)
    assert p4 == PerformanceProfile.HIGH

    p5 = HardwareDetector.determine_profile(cpu_count=8, ram_gb=16.0, gpu_available=True)
    assert p5 == PerformanceProfile.GPU_ACCELERATED


def test_capability_registry():
    reg = CapabilityRegistry()
    assert reg.is_available("filesystem")
    assert reg.is_available("shell")

    reg.register("test_cap", CapabilityStatus.AVAILABLE, "Test capability active")
    assert reg.is_available("test_cap")

    summary = reg.get_status_report()
    assert summary["total_capabilities"] > 5
    assert "test_cap" in summary["capabilities"]
