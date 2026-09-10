"""
Cross-platform storage information provider for JARVIS.
"""

import shutil
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class StorageInfo(BaseModel):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    total_gb: float
    used_gb: float
    free_gb: float


class StorageInfoProvider:
    """Retrieves disk usage and storage statistics without admin privileges."""

    @staticmethod
    def get_storage_info(target_path: Optional[Path] = None) -> StorageInfo:
        """Calculates disk space metrics for the volume containing target_path."""
        p = (target_path or Path(".")).resolve(strict=False)
        if not p.exists():
            p = Path(".").resolve(strict=False)

        usage = shutil.disk_usage(p)
        total = usage.total
        used = usage.used
        free = usage.free
        percent = (used / total * 100.0) if total > 0 else 0.0

        bytes_in_gb = 1024 ** 3

        return StorageInfo(
            path=str(p),
            total_bytes=total,
            used_bytes=used,
            free_bytes=free,
            percent_used=round(percent, 2),
            total_gb=round(total / bytes_in_gb, 2),
            used_gb=round(used / bytes_in_gb, 2),
            free_gb=round(free / bytes_in_gb, 2),
        )
