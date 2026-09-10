"""
Fact and Location Manager for JARVIS Memory Subsystem.
"""

from typing import List, Optional
from jarvis.memory.models import MemoryConfidence, MemoryItem, MemoryType, PrivacyLevel
from jarvis.memory.storage import MemoryStorage
from jarvis.memory.deduplication import MemoryDeduplicator


class FactManager:
    """Manages facts, locations, and personal profile information."""

    def __init__(self, storage: MemoryStorage, deduplicator: MemoryDeduplicator):
        self.storage = storage
        self.deduplicator = deduplicator

    def add_fact(self, key: str, content: str, fact_type: MemoryType = MemoryType.FACT) -> MemoryItem:
        item = MemoryItem(
            type=fact_type,
            key=key,
            content=content,
            source="USER_EXPLICIT",
            confidence=MemoryConfidence.EXPLICIT,
            importance=0.8,
            privacy_level=PrivacyLevel.PERSONAL,
        )
        resolved = self.deduplicator.process_and_deduplicate(item)
        self.storage.save_memory(resolved)
        return resolved

    def get_fact(self, key: str) -> Optional[str]:
        norm_key = self.deduplicator.normalize_key(key)
        item = self.storage.get_memory_by_key(norm_key)
        if item:
            self.storage.record_access(item.id, query=f"get_fact({key})")
            return item.content
        return None

    def list_facts(self) -> List[MemoryItem]:
        return self.storage.list_memories(memory_type=MemoryType.FACT)
