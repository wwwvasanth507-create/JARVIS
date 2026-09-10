"""
Hardware Detection & Adaptive Performance Tuning for JARVIS.

Inspects host environment (CPU, RAM, OS, GPU, audio, browser) and selects
an appropriate performance mode to ensure smooth CPU-first local execution.
"""

from enum import Enum
import os
import platform
import psutil
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PerformanceProfile(str, Enum):
    ULTRA_LOW = "ULTRA_LOW"          # <= 4GB RAM or <= 2 CPUs
    LOW = "LOW"                      # 4GB-8GB RAM or 4 CPUs
    MEDIUM = "MEDIUM"                # 8GB-16GB RAM
    HIGH = "HIGH"                    # > 16GB RAM + multi-core
    GPU_ACCELERATED = "GPU_ACCELERATED"  # Dedicated GPU available


class HardwareSpecs(BaseModel):
    cpu_count: int = Field(default_factory=os.cpu_count or 1)
    physical_cpu_count: int = Field(default=1)
    total_ram_gb: float = Field(default=8.0)
    available_ram_gb: float = Field(default=4.0)
    os_name: str = Field(default_factory=platform.system)
    gpu_available: bool = Field(default=False)
    gpu_device_name: Optional[str] = Field(default=None)
    audio_available: bool = Field(default=False)
    browser_available: bool = Field(default=False)
    ocr_available: bool = Field(default=False)
    vision_available: bool = Field(default=False)
    performance_profile: PerformanceProfile = Field(default=PerformanceProfile.MEDIUM)


class HardwareDetector:
    """Detects system hardware resources and selects safe runtime performance profile."""

    @classmethod
    def detect(cls) -> HardwareSpecs:
        cpu_count = os.cpu_count() or 1
        physical_cpu = cpu_count
        try:
            p_cpu = psutil.cpu_count(logical=False)
            if p_cpu:
                physical_cpu = p_cpu
        except Exception:
            pass

        total_ram = 8.0
        avail_ram = 4.0
        try:
            mem = psutil.virtual_memory()
            total_ram = round(mem.total / (1024 ** 3), 2)
            avail_ram = round(mem.available / (1024 ** 3), 2)
        except Exception as e:
            logger.warning(f"Could not read virtual memory via psutil: {e}")

        os_name = platform.system()

        # Check PyTorch / GPU availability if torch is present
        gpu_avail = False
        gpu_name = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_avail = True
                gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            pass

        # Audio check
        audio_avail = False
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            if len(devices) > 0:
                audio_avail = True
        except Exception:
            pass

        # Browser check (Playwright)
        browser_avail = False
        try:
            import playwright
            browser_avail = True
        except ImportError:
            pass

        # OCR check (pytesseract or easyocr)
        ocr_avail = False
        try:
            import pytesseract
            ocr_avail = True
        except ImportError:
            try:
                import easyocr
                ocr_avail = True
            except ImportError:
                pass

        # Determine mode
        profile = cls.determine_profile(cpu_count, total_ram, gpu_avail)

        specs = HardwareSpecs(
            cpu_count=cpu_count,
            physical_cpu_count=physical_cpu,
            total_ram_gb=total_ram,
            available_ram_gb=avail_ram,
            os_name=os_name,
            gpu_available=gpu_avail,
            gpu_device_name=gpu_name,
            audio_available=audio_avail,
            browser_available=browser_avail,
            ocr_available=ocr_avail,
            vision_available=ocr_avail,
            performance_profile=profile,
        )
        logger.info(f"Hardware detected: {specs.cpu_count} CPUs, {specs.total_ram_gb}GB RAM, OS: {specs.os_name}, Mode: {specs.performance_profile.value}")
        return specs

    @classmethod
    def determine_profile(cls, cpu_count: int, ram_gb: float, gpu_available: bool) -> PerformanceProfile:
        if gpu_available:
            return PerformanceProfile.GPU_ACCELERATED
        if ram_gb <= 4.0 or cpu_count <= 2:
            return PerformanceProfile.ULTRA_LOW
        if ram_gb <= 8.0 or cpu_count <= 4:
            return PerformanceProfile.LOW
        if ram_gb <= 16.0:
            return PerformanceProfile.MEDIUM
        return PerformanceProfile.HIGH
