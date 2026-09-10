"""
Retention Policy and Expiration Manager for JARVIS Memory Subsystem.
"""

import time
from typing import List
from jarvis.memory.storage import MemoryStorage


class RetentionManager:
    """Manages TTL cleanup and forget operations."""

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def cleanup_expired_memories(self) -> int:
        now = time.time()
        with self.storage.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
            conn.commit()
            return cur.rowcount

    def forget_key(self, key: str) -> bool:
        return self.storage.delete_memory_by_key(key)
