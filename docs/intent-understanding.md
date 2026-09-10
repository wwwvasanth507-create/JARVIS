# Intent Understanding & Resolution

The Intent subsystem (`src/jarvis/core/orchestration/intent.py`) parses raw user requests into structured `Intent` objects.

---

## Intent Schema

```json
{
  "intent_id": "uuid-v4",
  "action": "application.open",
  "target": "Chrome",
  "parameters": {
    "application": "Chrome"
  },
  "entities": ["Chrome"],
  "constraints": {},
  "confidence": "HIGH",
  "risk_level": "LOW",
  "requires_clarification": false,
  "is_fast_path": true,
  "direct_tool_name": "application.open"
}
```

---

## Deterministic Fast Path

For maximum responsiveness on CPU-only hardware, common action patterns bypass LLM parsing:

* **Applications**: "Open Chrome", "Close Calculator", "Is Spotify running?", "Focus VS Code", "List running applications"
* **Filesystem**: "List files in Downloads", "Search for *.pdf in Documents", "Read file notes.txt"
* **Computer**: "Show active window", "List windows"
* **Shell**: "Run command git status", "Check git status"
* **Browser**: "Open url https://github.com"

---

## Clarification Handling

When an intent or target is ambiguous (e.g. multiple candidate applications or ambiguous search targets), the intent parser sets `requires_clarification = True` and populates a `ClarificationRequest` object containing missing information and selectable candidate options, halting execution safely.
