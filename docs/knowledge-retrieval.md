# Knowledge Retrieval & Search

The Knowledge Retriever (`src/jarvis/memory/retrieval.py`) provides targeted excerpt retrieval for system tasks.

---

## Retrieval Flow

```text
Query ("local-first computer agent")
         ↓
Keyword Match across Index Excerpts
         ↓
Filter by Category (optional)
         ↓
Score & Rank Relevance
         ↓
Return Bounded Excerpt Snippets (Max 5 results)
```

Instead of injecting whole documents into prompt memory, only relevant section excerpts are formatted by `MemoryContextBuilder`.
