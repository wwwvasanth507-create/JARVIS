# JARVIS Memory Architecture 2.0

## Overview
JARVIS Memory Architecture 2.0 establishes a strict 6-layer memory model to ensure safe, contextual, and non-duplicative state management across sessions, tasks, and project interactions.

## Memory Layers

```
+-------------------------------------------------------------+
| 1. Working Memory (Session/Task Transient Context)         |
+-------------------------------------------------------------+
                              ↓
+-------------------------------------------------------------+
| 2. Task Memory (Episodic Completed Task Summaries)          |
+-------------------------------------------------------------+
                              ↓
+-------------------------------------------------------------+
| 3. Semantic Memory (Stable Facts & Environment Entities)   |
+-------------------------------------------------------------+
                              ↓
+-------------------------------------------------------------+
| 4. Preference Memory (Explicit & Inferred User Styles)     |
+-------------------------------------------------------------+
                              ↓
+-------------------------------------------------------------+
| 5. Project Memory (Workspace & Repository Contexts)         |
+-------------------------------------------------------------+
                              ↓
+-------------------------------------------------------------+
| 6. Knowledge Memory (Indexed Local Documents & Notes)      |
+-------------------------------------------------------------+
```

### Layer Definitions
1. **Working Memory**: Transient active request, goal, current plan, active entities, focused app/file, recent observations. Cleared automatically upon session expiration.
2. **Task Memory**: Structured summaries of finished tasks containing type, inputs, outputs, strategies, and outcome scores.
3. **Semantic Memory**: Stable environment facts (e.g. project roots, installed applications). Includes source provenance, confidence score, and creation/update timestamps.
4. **Preference Memory**: User preferences (language, output format, browser) with explicit levels (`EXPLICIT`, `STRONG_INFERENCE`, `WEAK_INFERENCE`) and scoped confidence decay.
5. **Project Memory**: Project repositories, root folders, commands, and associated tasks.
6. **Knowledge Memory**: Ingested markdown documents and user reference materials indexed incrementally with SHA-256 hashes.

## Provenance & Confidence Matrix
- `USER_EXPLICIT` (Trust: 1.0)
- `TOOL_VERIFIED` (Trust: 0.9)
- `USER_CORRECTED` (Trust: 0.95)
- `SYSTEM_OBSERVED` (Trust: 0.8)
- `TASK_OUTCOME` (Trust: 0.75)
- `INFERRED` (Trust: 0.5)
- `EXTERNAL_CONTENT` (Trust: 0.3)

## Security & Precedence Guarantee
Stored memory **NEVER** overrides:
1. Current User Instructions
2. Security & Permission Policies
3. System Safety Rules
