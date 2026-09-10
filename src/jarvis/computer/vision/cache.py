"""
Caching subsystem for screen OCR and visual analysis.
"""

from typing import Dict, Any, Optional
import time


class VisionCache:
    """
    Caches recent OCR and visual detection results keyed by screen perceptual hash.
    Automatically invalidates when screen hash changes or TTL expires.
    """

    def __init__(self, ttl_seconds: float = 30.0):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, screen_hash: str, key: str) -> Optional[Any]:
        if not screen_hash or screen_hash not in self._cache:
            return None
        entry = self._cache[screen_hash]
        if time.time() - entry.get("_timestamp", 0) > self.ttl_seconds:
            del self._cache[screen_hash]
            return None
        return entry.get(key)

    def set(self, screen_hash: str, key: str, value: Any) -> None:
        if not screen_hash:
            return
        if screen_hash not in self._cache:
            self._cache[screen_hash] = {"_timestamp": time.time()}
        self._cache[screen_hash][key] = value

    def clear(self) -> None:
        self._cache.clear()
