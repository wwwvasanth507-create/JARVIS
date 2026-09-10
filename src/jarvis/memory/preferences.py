"""
Preference Manager for JARVIS Memory Subsystem.
"""

from typing import Dict, Optional
from jarvis.memory.models import MemoryConfidence, MemoryItem, MemoryType, PrivacyLevel
from jarvis.memory.storage import MemoryStorage
from jarvis.memory.deduplication import MemoryDeduplicator


class PreferenceManager:
    """Manages user preference memory records."""

    def __init__(self, storage: MemoryStorage, deduplicator: MemoryDeduplicator):
        self.storage = storage
        self.deduplicator = deduplicator

    def set_preference(self, key: str, value: str, source: str = "USER_EXPLICIT") -> MemoryItem:
        item = MemoryItem(
            type=MemoryType.PREFERENCE,
            key=f"pref_{key}",
            content=value,
            metadata={"pref_name": key},
            source=source,
            confidence=MemoryConfidence.EXPLICIT,
            importance=1.0,
            privacy_level=PrivacyLevel.PERSONAL,
        )
        resolved = self.deduplicator.process_and_deduplicate(item)
        self.storage.save_memory(resolved)
        return resolved

    def get_preference(self, key: str) -> Optional[str]:
        item = self.storage.get_memory_by_key(f"pref_{key}")
        if not item:
            item = self.storage.get_memory_by_key(key)
        if item:
            self.storage.record_access(item.id, query=f"get_preference({key})")
            return item.content
        return None

    def list_preferences(self) -> Dict[str, str]:
        items = self.storage.list_memories(memory_type=MemoryType.PREFERENCE)
        prefs = {}
        for it in items:
            p_name = it.metadata.get("pref_name", it.key.replace("pref_", ""))
            prefs[p_name] = it.content
        return prefs
