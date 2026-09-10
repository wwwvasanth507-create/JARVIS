# JARVIS Long-Running Task Subsystem

## Task Structure & Lifecycle (`src/jarvis/core/tasks/task_manager.py`)
Tracks long-running computer-use tasks across 13 statuses (`CREATED`, `QUEUED`, `RUNNING`, `WAITING_FOR_USER`, `WAITING_FOR_CONFIRMATION`, `PAUSED`, `RECOVERING`, `DEGRADED`, `COMPLETED`, `PARTIAL_SUCCESS`, `FAILED`, `CANCELLED`, `EXPIRED`).

### Features:
- **Task Heartbeats (`TaskHeartbeat`)**: Tracks `last_progress_time`, `last_state_change`, `last_tool_call`, and `verification_success`.
- **Worker Leases**: Prevents duplicate worker execution using time-bounded task leases.
- **Idempotency Keys**: Prevents duplicate task execution when identical tasks are submitted concurrently.
- **Environment Fingerprints**: Captures active app, window title, target file existence, network availability, and model availability.
