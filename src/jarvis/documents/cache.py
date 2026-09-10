"""
Local document caching infrastructure.
"""

from typing import Dict, Any, Optional
from jarvis.documents.models import DocumentInfo, DocumentStructure, DocumentSummary


class DocumentCache:
    """
    In-memory document cache keyed by content_hash.
    Automatically invalidates when content hash changes.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, content_hash: str, key: str) -> Optional[Any]:
        if not self.enabled or content_hash not in self._cache:
            return None
        return self._cache[content_hash].get(key)

    def set(self, content_hash: str, key: str, value: Any) -> None:
        if not self.enabled:
            return
        if content_hash not in self._cache:
            self._cache[content_hash] = {}
        self._cache[content_hash][key] = value

    def invalidate(self, content_hash: str) -> None:
        if content_hash in self._cache:
            del self._cache[content_hash]

    def clear(self) -> None:
        self._cache.clear()
