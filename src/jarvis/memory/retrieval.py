"""
Memory and Knowledge Retrieval Engine for JARVIS.
"""

import json
from typing import List, Optional
from jarvis.memory.database import DatabaseManager
from jarvis.memory.models import KnowledgeQueryResult, MemoryItem, MemoryType
from jarvis.memory.ranking import MemoryRanker
from jarvis.memory.storage import MemoryStorage


class MemoryRetriever:
    """Retrieves relevant memory items for user requests."""

    def __init__(self, storage: MemoryStorage, ranker: Optional[MemoryRanker] = None):
        self.storage = storage
        self.ranker = ranker or MemoryRanker()

    def retrieve(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
    ) -> List[MemoryItem]:
        all_memories = self.storage.list_memories(memory_type=memory_type, limit=200)
        if not all_memories:
            return []

        ranked = self.ranker.rank_memories(all_memories, query)
        
        # Conflict resolution: deduplicate conflicting preferences/facts, keeping newest created_at
        seen_keys = {}
        conflict_resolved = []
        for item in ranked:
            key = item.key if hasattr(item, 'key') and item.key else item.content[:30]
            if key not in seen_keys:
                seen_keys[key] = item
                conflict_resolved.append(item)

        results = conflict_resolved[:limit]

        # Record access for retrieved items
        for item in results:
            self.storage.record_access(item.id, query=query)

        return results


class KnowledgeRetriever:
    """Searches indexed Markdown knowledge documents."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_mgr = db_manager

    def search(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[KnowledgeQueryResult]:
        keywords = [w.lower() for w in query.split() if len(w) > 2]
        if not keywords:
            return []

        results = []
        with self.db_mgr.get_connection() as conn:
            cur = conn.cursor()
            sql = """
            SELECT d.document_id, d.title, d.path, d.category, i.section_title, i.content_excerpt
            FROM knowledge_indexes i
            JOIN knowledge_documents d ON i.document_id = d.document_id
            """
            params = []
            if category:
                sql += " WHERE LOWER(d.category) = LOWER(?)"
                params.append(category)

            cur.execute(sql, params)
            rows = cur.fetchall()

            for row in rows:
                text = f"{row['title']} {row['section_title']} {row['content_excerpt']}".lower()
                matches = sum(1 for kw in keywords if kw in text)
                if matches > 0:
                    score = matches / len(keywords)
                    results.append(
                        KnowledgeQueryResult(
                            document_id=row["document_id"],
                            title=row["title"],
                            path=row["path"],
                            category=row["category"],
                            excerpt=f"[{row['section_title']}] {row['content_excerpt'][:250]}...",
                            relevance_score=round(score, 4),
                        )
                    )

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]
