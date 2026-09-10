"""
Observation Cache with Freshness Validation & Mandatory Pre-Action Re-Observation for JARVIS.
"""

import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CachedObservation(BaseModel):
    key: str
    data: Any
    timestamp: float = Field(default_factory=time.time)
    ttl_sec: float = 30.0
    source: str = "tool"


class ObservationCache:
    """Bounded observation cache enforcing TTL freshness and pre-action re-observation."""

    _instance: Optional["ObservationCache"] = None

    def __init__(self):
        self._cache: Dict[str, CachedObservation] = {}

    @classmethod
    def get_instance(cls) -> "ObservationCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def put(self, key: str, data: Any, ttl_sec: float = 30.0, source: str = "tool") -> None:
        self._cache[key] = CachedObservation(key=key, data=data, ttl_sec=ttl_sec, source=source)

    def get(self, key: str) -> Optional[Any]:
        obs = self._cache.get(key)
        if not obs:
            return None
        if time.time() - obs.timestamp > obs.ttl_sec:
            logger.info(f"ObservationCache key '{key}' expired (TTL={obs.ttl_sec}s). Invalidating.")
            del self._cache[key]
            return None
        return obs.data

    def invalidate(self, key: Optional[str] = None) -> None:
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    def requires_reobservation(self, tool_name: str, key: str) -> bool:
        """Determines if a critical side-effect tool requires fresh state re-observation."""
        CRITICAL_TOOLS = ("filesystem.delete", "shell.execute", "browser.submit_form", "application.close")
        if any(c in tool_name for c in CRITICAL_TOOLS):
            data = self.get(key)
            return data is None
        return False
