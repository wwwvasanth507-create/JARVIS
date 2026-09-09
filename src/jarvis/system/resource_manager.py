"""
Resource Manager Module for monitoring CPU/RAM usage and throttling background tasks.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import platform
import subprocess


class SystemResourceStatus(BaseModel):
    cpu_percent: float = Field(default=0.0, description="Current estimated CPU utilization percentage")
    ram_used_gb: float = Field(default=0.0)
    ram_total_gb: float = Field(default=8.0)
    ram_percent: float = Field(default=0.0)
    active_tasks: int = Field(default=0)
    background_indexing_paused: bool = Field(default=False)


class ResourceManager:
    """Monitors system load and throttles background activities when resource thresholds are exceeded."""

    def __init__(self, high_cpu_threshold: float = 85.0, high_ram_threshold: float = 90.0):
        self.high_cpu_threshold = high_cpu_threshold
        self.high_ram_threshold = high_ram_threshold
        self._background_paused = False

    def get_status(self, active_task_count: int = 0) -> SystemResourceStatus:
        cpu_percent = 15.0
        ram_used = 4.0
        ram_total = 8.0
        ram_percent = 50.0

        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            ram_used = round((mem.total - mem.available) / (1024**3), 2)
            ram_total = round(mem.total / (1024**3), 2)
            ram_percent = mem.percent
        except ImportError:
            pass

        # Check threshold overload
        should_pause = (cpu_percent >= self.high_cpu_threshold) or (ram_percent >= self.high_ram_threshold)
        self._background_paused = should_pause

        return SystemResourceStatus(
            cpu_percent=cpu_percent,
            ram_used_gb=ram_used,
            ram_total_gb=ram_total,
            ram_percent=ram_percent,
            active_tasks=active_task_count,
            background_indexing_paused=self._background_paused,
        )

    def is_throttled(self) -> bool:
        return self._background_paused
