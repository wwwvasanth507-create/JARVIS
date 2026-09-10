"""
Memory Deduplication and Conflict Resolution for JARVIS.
"""

import re
import time
from typing import Optional
from jarvis.memory.models import MemoryConfidence, MemoryItem
from jarvis.memory.storage import MemoryStorage


class MemoryDeduplicator:
    """Normalizes keys and resolves memory conflicts."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def normalize_key(self, raw_key: str) -> str:
        k = raw_key.strip().lower()
        k = re.sub(r"[^\w\.-]", "_", k)
        return re.sub(r"_+", "_", k).strip("_")

    def process_and_deduplicate(self, new_item: MemoryItem) -> MemoryItem:
        normalized_key = self.normalize_key(new_item.key)
        new_item.key = normalized_key

        existing = self.storage.get_memory_by_key(normalized_key)
        if not existing:
            return new_item

        # Conflict resolution logic:
        # 1. EXPLICIT confidence supersedes lower confidence
        # 2. Equal or higher confidence -> update content, update timestamp
        if (
            new_item.confidence == MemoryConfidence.EXPLICIT
            or existing.confidence != MemoryConfidence.EXPLICIT
        ):
            existing.content = new_item.content
            existing.metadata.update(new_item.metadata)
            existing.updated_at = time.time()
            existing.source = new_item.source
            existing.confidence = new_item.confidence
            return existing

        return new_item
