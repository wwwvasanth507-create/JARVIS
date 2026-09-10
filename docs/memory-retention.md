# Memory Retention & Expiration

The Retention Manager (`src/jarvis/memory/retention.py`) handles memory lifecycle management, expiration timeouts (`expires_at`), and user-directed forget commands.

---

## Retention Policies

1. **Explicit Preferences & Facts**: No automatic expiration (`expires_at = None`).
2. **Temporary Tasks / Context**: Configurable TTL expiration timestamp.
3. **Automated Cleanup**: `cleanup_expired_memories()` purges records where `expires_at < current_timestamp`.
4. **Explicit Forgetting**: `MemoryManager.forget(key)` removes or deactivates target memory items completely.
