# JARVIS Conversation Context System

## Overview
The Conversation Context system manages active task state, active entity tracking, pronoun and ordinal reference resolution, and pending clarification states across user interactions.

---

## Architecture

```
User Query ("play the second one")
    ↓
ConversationStateManager (inspects recent_tool_outputs)
    ↓
ReferenceResolver (resolves ordinal -> "https://youtube.com/watch?v=2")
    ↓
ToolDispatcher / Orchestrator
```

## Privacy & Security Policy
- Temporary conversational state is bounded (max 15 entities, max 10 tool outputs).
- No secrets, credentials, or sensitive tokens are stored in active state.
- `state_mgr.reset()` completely clears active conversation state.
