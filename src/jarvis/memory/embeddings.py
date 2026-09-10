"""
CPU-friendly Local Text Embedding Abstraction for JARVIS.
"""

import math
import re
from typing import List, Optional


class EmbeddingProvider:
    """Provides local text embedding vectors with keyword TF-IDF fallback."""

    def __init__(self, model_name: str = "cpu_fallback"):
        self.model_name = model_name

    def is_available(self) -> bool:
        return True

    def model_info(self) -> dict:
        return {"model_name": self.model_name, "vector_dim": 128, "type": "local_cpu"}

    def embed(self, text: str) -> List[float]:
        # Lightweight term-frequency hash vector representation (128-dim)
        vec = [0.0] * 128
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec

        for word in words:
            idx = abs(hash(word)) % 128
            vec[idx] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        return sum(a * b for a, b in zip(vec1, vec2))
