# JARVIS Agent Intelligence Architecture

## Overview
Prompt 019 introduces production-grade agent intelligence, hierarchical execution routing, reference resolution, first-class ambiguity management, plan quality validation, prompt injection defense, and interrupted task persistence to JARVIS without introducing cloud dependencies, external APIs, or unnecessary LLM calls.

---

## Key Components

### 1. Conversation State Manager (`ConversationStateManager`)
- Maintains a bounded, privacy-filtered state tracking:
  - `active_request`, `active_goal`
  - `active_application`
  - `active_browser_page` (URL, title, search results)
  - `active_file` (recent document/file paths)
  - `active_entities` (up to 15 recent entities with timestamps and metadata)
  - `recent_tool_outputs` (up to 10 recent tool execution outputs)

### 2. Contextual Reference Resolver (`ReferenceResolver`)
- Resolves conversational references against active state:
  - **Pronouns**: "it", "that", "this", "the file", "the report", "the browser", "the app"
  - **Ordinals**: "the 1st result", "play the second song", "the third file"
- Replaces ambiguous placeholders with verified concrete entity paths or URLs.

### 3. Structured Ambiguity & Targeted Clarification (`AmbiguityHandler`)
- Converts ambiguous user requests with multiple valid targets into `StructuredAmbiguity` objects:
  - Generates specific, friendly questions: `"I found 3 matching files for 'report.pdf': 1. Downloads\report.pdf, 2. Documents\report.pdf. Which one should I open, Boss?"`
  - Stores pending clarification state until user answers ("the first one" or "Downloads").

### 4. Hierarchical Execution Router (`HierarchicalRouter`)
- Evaluates incoming requests through a low-latency, CPU-first hierarchy:
  1. `FAST_PATH`: Direct tool mappings (e.g. "Open Chrome", "Close window")
  2. `DETERMINISTIC`: Keyword / rule-based regex parsing
  3. `SKILL_RESOLVER`: Registered skill capability matches
  4. `CONTEXTUAL_RESOLVER`: State reference resolution
  5. `LOCAL_LLM`: GGUF model reasoning for complex requests
  6. `VISUAL_REASONING`: Screen OCR / vision model as final fallback

### 5. Plan Quality Scorer (`PlanQualityScorer`)
- Validates multi-step execution plans before dispatch:
  - Scores plans for dependency completeness, valid tool names, risk levels, and permission compatibility.
  - Rejects plans with unspecified tools, missing dependencies, or unverified high-risk actions.

### 6. Prompt Injection Defense (`PromptInjectionDefense`)
- Scans external web page text, document excerpts, and memory items for injection patterns (e.g. "Ignore previous instructions", "Bypass security rules").
- Encapsulates untrusted external text in `[UNTRUSTED CONTENT PAYLOAD (...)]` blocks to prevent model authority hijacking.

### 7. Interrupted Task Resume Manager (`TaskResumeManager`)
- Saves checkpoint snapshots (`TaskCheckpoint`) of multi-step workflows during clean shutdown or unexpected restart.
- Enables safe post-restart task inspection and user resume/abort protocol.
