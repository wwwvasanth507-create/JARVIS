# JARVIS — Persistent Memory & Knowledge Architecture

The Memory & Knowledge subsystem (`src/jarvis/memory/`) provides local-first, privacy-preserving, CPU-optimized persistent storage for personal context, user preferences, projects, tasks, episodic event histories, and structured Markdown knowledge bases.

---

## Architecture Overview

```text
User / Orchestrator
         ↓
   MemoryManager (Facade)
         │
   ┌─────┴─────────────────────────┬─────────────────────────┐
   ▼                               ▼                         ▼
MemoryStorage (SQLite)     KnowledgeIndexer (SHA256)   MemoryPrivacyPolicy
   │                               │                         │
   ├── Preferences & Facts         ├── Document Hash         └── Secret Blocking
   ├── Projects & Tasks            ├── Section Extraction        (Passwords, Tokens,
   ├── Episodes & Summaries        └── Keyword Indexing           API Keys)
   └── Hybrid Retriever
```

---

## Key Capabilities

1. **SQLite Database Storage**: Zero cloud server dependency (`data/database/memory.db`).
2. **Explicit Memory Categories**: `FACT`, `PREFERENCE`, `PROFILE`, `PROJECT`, `LOCATION`, `TASK`, `EPISODIC`, `CONVERSATION_SUMMARY`, `SYSTEM_CONTEXT`.
3. **Secret & Privacy Protection**: Automatic pattern matching rejecting passwords, API keys, bearer tokens, private keys, and credit cards.
4. **Conflict Resolution & Deduplication**: Key normalization and confidence-weighted updates (Explicit statements supersede inferred records).
5. **Incremental Knowledge Indexing**: Content hashing (SHA256) scanning Markdown documentation without loading entire libraries into RAM.
6. **Bounded Context Formatting**: `MemoryContextBuilder` packing relevant memories and excerpts into compact prompt contexts (`< 12,000` chars).
7. **Permission Isolation**: Memory provides context, NEVER permission authorization.
