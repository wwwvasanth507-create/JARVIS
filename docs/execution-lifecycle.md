# Execution State Lifecycle

Every user request processed by `JarvisOrchestrator` transitions through structured execution states (`src/jarvis/core/orchestration/state.py`).

---

## State Diagram

```text
       [PLANNING]
           │
  ┌────────┴────────┐
  ▼                 ▼
[NEEDS_CLARIFICATION]  [EXECUTING] ◄────► [WAITING_FOR_CONFIRMATION]
                        │    │
            ┌───────────┘    └───────────┐
            ▼                            ▼
      [VERIFYING]                   [RECOVERING]
            │                            │
   ┌────────┴────────┐                   │
   ▼                 ▼                   │
[COMPLETED]       [FAILED] ◄─────────────┘
                     ▲
                     │
                [CANCELLED]
```

---

## State Descriptions

* `PLANNING`: Request normalization, intent parsing, goal construction, plan generation, policy validation.
* `NEEDS_CLARIFICATION`: Execution paused due to ambiguous intent or missing targets.
* `WAITING_FOR_CONFIRMATION`: Execution paused pending valid confirmation token for HIGH/CRITICAL risk action.
* `EXECUTING`: Tool dispatched and actively running.
* `VERIFYING`: Post-condition validation executing.
* `RECOVERING`: Bounded step retry or replanning in progress.
* `COMPLETED`: Terminal state; all plan steps verified successfully.
* `FAILED`: Terminal state; step or verification failed.
* `CANCELLED`: Terminal state; user issued interrupt signal.
