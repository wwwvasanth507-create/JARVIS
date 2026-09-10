# JARVIS Task Execution & Progress Tracking

## Execution Lifecycle & Status Model

Structured execution states:
- `TASK RECEIVED` -> `UNDERSTANDING` -> `PLANNING` -> `WAITING_FOR_CLARIFICATION` -> `WAITING_FOR_CONFIRMATION` -> `EXECUTING` -> `VERIFYING` -> `RECOVERING` -> `COMPLETED`

## Partial Success Handling
- Tasks distinguish `SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `CANCELLED`, `BLOCKED`, and `WAITING_FOR_USER`.
- Detailed summaries clearly explain which steps succeeded and which failed (e.g. document read succeeded, save failed due to read-only folder).

## Interrupted Task Resume (`TaskResumeManager`)
- Persists execution state to `data/cache/interrupted_tasks.json`.
- Post-restart inspection prompts Boss before re-executing safe pending steps.
