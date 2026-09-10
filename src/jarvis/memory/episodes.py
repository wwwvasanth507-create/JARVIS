"""
Episodic Memory Manager for JARVIS Memory Subsystem.
"""

from typing import List
from jarvis.memory.models import Episode
from jarvis.memory.storage import MemoryStorage


class EpisodeManager:
    """Manages significant event log records."""

    MIN_EPISODE_IMPORTANCE = 0.4

    def __init__(self, storage: MemoryStorage):
        self.storage = storage

    def record_episode(
        self,
        description: str,
        importance: float = 0.5,
        subsystem: str = "generic",
        action: str = "observation",
    ) -> bool:
        if importance < self.MIN_EPISODE_IMPORTANCE:
            return False

        ep = Episode(
            description=description,
            importance=importance,
            subsystem=subsystem,
            action=action,
        )

        with self.storage.db_mgr.get_connection() as conn:
            conn.execute(
                "INSERT INTO episodes (id, description, importance, subsystem, action, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ep.id, ep.description, ep.importance, ep.subsystem, ep.action, ep.created_at),
            )
            conn.commit()
        return True

    def list_recent_episodes(self, limit: int = 20) -> List[Episode]:
        with self.storage.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM episodes ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [
                Episode(
                    id=r["id"],
                    description=r["description"],
                    importance=r["importance"],
                    subsystem=r["subsystem"],
                    action=r["action"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
