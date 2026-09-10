"""
Controlled application discovery engine and cache index manager for JARVIS.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from jarvis.applications.platform import ApplicationPlatform
from jarvis.applications.state import ApplicationInfo


class ApplicationCache(BaseModel):
    last_updated: str
    platform: str
    discovered_count: int
    applications: List[ApplicationInfo]


class ApplicationDiscovery:
    """Discovers installed applications natively and maintains data/indexes/applications.json."""

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or Path("data/indexes/applications.json")

    def load_cache(self) -> Optional[ApplicationCache]:
        """Loads cached discovery results from disk."""
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ApplicationCache(**data)
        except Exception:
            return None

    def save_cache(self, cache: ApplicationCache) -> None:
        """Saves discovery cache to data/indexes/applications.json."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache.model_dump(), f, indent=2)

    def discover_applications(self, known_apps: List[ApplicationInfo]) -> List[ApplicationInfo]:
        """
        Scans standard OS discovery locations for installed executables matching known registry entries.
        """
        discovered: List[ApplicationInfo] = []

        for app in known_apps:
            resolved_p = ApplicationPlatform.resolve_executable_path(app)
            if resolved_p:
                app_copy = app.model_copy()
                app_copy.executable_path = str(resolved_p)
                discovered.append(app_copy)

        now_str = datetime.now(timezone.utc).isoformat()
        cache = ApplicationCache(
            last_updated=now_str,
            platform=ApplicationPlatform.get_platform_name(),
            discovered_count=len(discovered),
            applications=discovered,
        )
        self.save_cache(cache)

        return discovered
