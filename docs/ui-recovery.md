# UI Recovery & Stale Handle Defense

JARVIS handles UI staleness, missing targets, application restarts, and manual user takeover.

## Stale Handle Defense

- Stores durable semantic target queries (`TargetQuery`) and paths rather than raw ephemeral element pointers.
- Automatically re-evaluates snapshot and re-resolves targets if Playwright DOM handles or Windows UIA elements become stale.

## Bounded Semantic Recovery

When a target element is missing or moves:
1. Re-captures fresh `ScreenSemanticSnapshot`.
2. Re-runs ranked semantic search across perception providers.
3. If user manually intervened (detected via state hash mismatch or takeover monitor), pauses execution, reconciles UI state, and replans safely.
