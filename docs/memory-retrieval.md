# Memory Retrieval & Hybrid Ranking

The Retrieval Engine (`src/jarvis/memory/retrieval.py`, `ranking.py`) uses a multi-signal scoring algorithm to select the most relevant memories for prompt context injection.

---

## Scoring Formula

```text
Relevance Score = 0.5 * (Keyword Match Ratio)
                + 0.2 * (Confidence Weight)
                + 0.2 * (Recency Decay)
                + 0.1 * (Access Frequency Bonus)
```

---

## Ranking Weights

* **Explicit Confidence**: `1.0`
* **High Confidence**: `0.8`
* **Medium Confidence**: `0.6`
* **Low Confidence**: `0.4`
* **Recency Decay**: Linear decay over 30 days
