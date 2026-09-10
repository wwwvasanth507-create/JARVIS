# Task Scheduler Architecture

## Component Pipeline
```
User / Skill Request
 ↓
ScheduleParser (natural language resolution)
 ↓
ScheduledTask (persisted to SQLite via TaskPersistence)
 ↓
TaskScheduler (event-driven wait loop)
 ↓
TaskWorkerPool (bounded async thread pool)
 ↓
TaskExecutor (runtime permission evaluation)
 ↓
JarvisOrchestrator → PlanExecutor → Verification → Prompt 015 Recovery
```

## Key Components
- `SchedulerManager`: Main facade for creating, updating, pausing, resuming, cancelling, and deleting tasks.
- `ScheduleParser`: Resolves relative time offsets, exact times, and recurring patterns.
- `TaskPersistence`: Manages `scheduled_tasks` and `task_runs` in SQLite (`data/database/memory.db`).
- `TaskScheduler`: Thread event loop sleeping on condition wake until `next_run_at`.
- `TaskWorkerPool`: Bounded async worker queue (`max_concurrent_tasks: 2`).
- `TaskExecutor`: Dispatches tasks through `JarvisOrchestrator` with runtime permission re-evaluations.
- `NotificationManager`: Multi-channel notification delivery (Text -> Desktop -> Voice fallback).
- `SchedulerPolicy`: Enforces missed-task policy (`skip`), overlap policy (`skip`), and recurring failure threshold (`3` failures -> auto-pause).
