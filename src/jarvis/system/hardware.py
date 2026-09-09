"""
Hardware Detection and Profiling Subsystem for JARVIS.
"""

from enum import Enum
import os
import platform
import shutil
import subprocess
import sys
from typing import Optional
from pydantic import BaseModel, Field


class HardwareProfileTier(str, Enum):
    ULTRA_LOW = "ULTRA_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    GPU_ACCELERATED = "GPU_ACCELERATED"


class HardwareProfile(BaseModel):
    cpu_name: str = Field(default="Unknown CPU")
    physical_cores: int = Field(default=1)
    logical_cores: int = Field(default=1)
    ram_gb: float = Field(default=4.0)
    gpu_available: bool = Field(default=False)
    gpu_name: str = Field(default="Integrated/None")
    vram_gb: float = Field(default=0.0)
    cpu_only: bool = Field(default=True)
    os_name: str = Field(default=platform.system())
    available_disk_gb: float = Field(default=10.0)
    profile_tier: HardwareProfileTier = Field(default=HardwareProfileTier.LOW)


class HardwareDetector:
    """Detects physical system hardware and assigns an operational performance tier."""

    @staticmethod
    def detect() -> HardwareProfile:
        logical_cores = os.cpu_count() or 1
        physical_cores = max(1, logical_cores // 2)
        cpu_name = platform.processor() or "Generic x86_64 CPU"
        ram_gb = 8.0
        gpu_available = False
        gpu_name = "Integrated/None"
        vram_gb = 0.0
        os_name = f"{platform.system()} {platform.release()}"

        # Disk space check
        try:
            total, used, free = shutil.disk_usage(".")
            available_disk_gb = round(free / (1024**3), 2)
        except Exception:
            available_disk_gb = 20.0

        # Memory detection (Windows CIM / psutil fallback)
        try:
            import psutil
            mem = psutil.virtual_memory()
            ram_gb = round(mem.total / (1024**3), 2)
        except ImportError:
            if platform.system() == "Windows":
                try:
                    out = subprocess.check_output(
                        ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                        text=True,
                        stderr=subprocess.DEVNULL,
                    )
                    lines = [line.strip() for line in out.splitlines() if line.strip().isdigit()]
                    if lines:
                        ram_gb = round(int(lines[0]) / (1024**3), 2)
                except Exception:
                    pass

        # CPU Name refinement on Windows
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["wmic", "cpu", "get", "name,NumberOfCores,NumberOfLogicalProcessors"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                lines = [line.strip() for line in out.splitlines() if line.strip() and not line.startswith("Name")]
                if lines:
                    parts = lines[0].rsplit(None, 2)
                    if len(parts) >= 3:
                        cpu_name = parts[0].strip()
                        physical_cores = int(parts[1])
                        logical_cores = int(parts[2])
            except Exception:
                pass

        # GPU detection (check nvidia-smi or ROCm/torch/vulkan)
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=gpu_name,memory.total", "--format=csv,noheader,nounits"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            parts = [p.strip() for p in out.splitlines()[0].split(",")]
            if len(parts) >= 2:
                gpu_available = True
                gpu_name = parts[0]
                vram_gb = round(float(parts[1]) / 1024, 2)
        except Exception:
            gpu_available = False

        cpu_only = not gpu_available

        # Classify Hardware Tier
        tier = HardwareDetector._classify_tier(
            ram_gb=ram_gb,
            physical_cores=physical_cores,
            gpu_available=gpu_available,
            vram_gb=vram_gb,
        )

        return HardwareProfile(
            cpu_name=cpu_name,
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            ram_gb=ram_gb,
            gpu_available=gpu_available,
            gpu_name=gpu_name,
            vram_gb=vram_gb,
            cpu_only=cpu_only,
            os_name=os_name,
            available_disk_gb=available_disk_gb,
            profile_tier=tier,
        )

    @staticmethod
    def _classify_tier(
        ram_gb: float,
        physical_cores: int,
        gpu_available: bool,
        vram_gb: float,
    ) -> HardwareProfileTier:
        if gpu_available and vram_gb >= 6.0:
            return HardwareProfileTier.GPU_ACCELERATED
        if ram_gb <= 4.0 or physical_cores <= 2:
            return HardwareProfileTier.ULTRA_LOW
        if ram_gb <= 8.0 or physical_cores <= 4:
            return HardwareProfileTier.LOW
        if ram_gb <= 16.0:
            return HardwareProfileTier.MEDIUM
        return HardwareProfileTier.HIGH
