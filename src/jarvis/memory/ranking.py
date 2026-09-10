"""
Hybrid Relevance Ranking for JARVIS Memory Subsystem.
"""

import time
from typing import List
from jarvis.memory.models import MemoryItem, MemoryConfidence


class MemoryRanker:
    """Ranks retrieved memory items using multi-signal scoring."""

    CONFIDENCE_WEIGHTS = {
        MemoryConfidence.EXPLICIT: 1.0,
        MemoryConfidence.HIGH: 0.8,
        MemoryConfidence.MEDIUM: 0.6,
        MemoryConfidence.LOW: 0.4,
    }

    def score_memory(self, item: MemoryItem, query_keywords: List[str]) -> float:
        score = 0.0

        # 1. Keyword match score
        text = f"{item.key} {item.content}".lower()
        if query_keywords:
            matches = sum(1 for kw in query_keywords if kw in text)
            score += (matches / len(query_keywords)) * 0.5

        # 2. Confidence score
        conf_weight = self.CONFIDENCE_WEIGHTS.get(item.confidence, 0.5)
        score += conf_weight * 0.2

        # 3. Recency score (decay over 30 days)
        age_hours = (time.time() - item.updated_at) / 3600.0
        recency = max(0.0, 1.0 - (age_hours / (24.0 * 30.0)))
        score += recency * 0.2

        # 4. Access frequency score
        access_bonus = min(1.0, item.access_count / 10.0)
        score += access_bonus * 0.1

        return round(score, 4)

    def rank_memories(self, items: List[MemoryItem], query: str) -> List[MemoryItem]:
        keywords = [w.lower() for w in query.split() if len(w) > 2]
        scored = [(item, self.score_memory(item, keywords)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored]
