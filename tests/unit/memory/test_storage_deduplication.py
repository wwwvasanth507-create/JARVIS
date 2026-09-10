"""
Unit tests for MemoryStorage and MemoryDeduplicator.
"""

from jarvis.memory.database import DatabaseManager
from jarvis.memory.deduplication import MemoryDeduplicator
from jarvis.memory.migrations import SchemaMigrator
from jarvis.memory.models import MemoryConfidence, MemoryItem, MemoryType
from jarvis.memory.storage import MemoryStorage


def test_storage_crud_and_deduplication():
    db_mgr = DatabaseManager(db_path=":memory:")
    SchemaMigrator(db_mgr).migrate()
    storage = MemoryStorage(db_mgr)
    dedup = MemoryDeduplicator(storage)

    item1 = MemoryItem(
        type=MemoryType.PREFERENCE,
        key="preferred_browser",
        content="Chrome",
        confidence=MemoryConfidence.EXPLICIT,
    )
    resolved1 = dedup.process_and_deduplicate(item1)
    storage.save_memory(resolved1)

    fetched = storage.get_memory_by_key("preferred_browser")
    assert fetched is not None
    assert fetched.content == "Chrome"

    # Save new contradictory explicit statement -> should overwrite
    item2 = MemoryItem(
        type=MemoryType.PREFERENCE,
        key="preferred_browser",
        content="Firefox",
        confidence=MemoryConfidence.EXPLICIT,
    )
    resolved2 = dedup.process_and_deduplicate(item2)
    storage.save_memory(resolved2)

    fetched2 = storage.get_memory_by_key("preferred_browser")
    assert fetched2 is not None
    assert fetched2.content == "Firefox"
