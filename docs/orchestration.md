# JARVIS — Intent Understanding, Planning & Tool Orchestration Layer

The Orchestration Layer in `src/jarvis/core/orchestration/` acts as the central intelligence dispatch hub for JARVIS. It translates high-level natural language requests into structured intents, goals, and multi-step plans, evaluates permissions, dispatches tools from the tool registry, collects observations, enforces mandatory post-condition verification, and handles bounded retries and user confirmations.

---

## Key Features

1. **Deterministic Fast-Path**: Direct command routing for unambiguous requests ("Open Chrome", "List files") bypassing expensive LLM reasoning loops.
2. **Structured Intent & Goal Resolution**: Formal representation of user intent (`Intent`) and objectives (`Goal`) with explicit target parameters and constraints.
3. **Plan Generation & Safety Validation**: Multi-step plan creation (`Plan`, `PlanStep`) with static validation (`PlanValidator`) checking schema compatibility, tool availability, and prohibited tool sequences.
4. **Security Integration**: Strict evaluation via `PermissionEvaluator` preventing privilege escalation and tool chaining bypasses.
5. **Confirmation Token Lifecycle**: Tokenized confirmation flow for HIGH and CRITICAL risk actions with automatic expiration timeouts.
6. **Honest Post-Condition Verification**: Verification manager (`VerificationManager`) that validates actual system state post-execution and refuses to report fake success.
7. **Bounded Recovery & Loop Prevention**: Single-retry step recovery, replan limits, and automatic detection of repeating failing execution loops.
8. **Cancellation Support**: Real-time interrupt handling for cancellation keywords ("stop", "cancel", "never mind").

---

## Architecture Flow

```text
User Request / Voice Input
         ↓
Intent Parser (Fast-Path / LLM Fallback)
         ↓
Goal Resolver
         ↓
Planner (Step Generation & Dependency Graph)
         ↓
Plan Validator (Security & Schema Verification)
         ↓
Plan Executor
    ├── Confirmation Check (HIGH/CRITICAL Risk)
    ├── Tool Dispatcher (Registry Execution)
    ├── Observation Manager (Subsystem State Capture)
    ├── Verification Manager (State Post-Condition Check)
    └── Recovery Manager (Retry / Loop Detection)
         ↓
Execution State Result & Audit History
```
