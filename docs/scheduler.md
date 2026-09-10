# Task Scheduler & Background Automation Architecture

## Overview
The Task Scheduler subsystem (`src/jarvis/scheduler/`) provides local, CPU-friendly task scheduling, background execution, natural-language expression parsing, SQLite persistence, runtime security re-evaluation, notification delivery, and closed-loop self-recovery.

## Core Features
- **Deterministic Natural-Language Parser**: Resolves relative time offsets ("in 30 minutes"), exact times ("tomorrow at 9 AM"), and recurring patterns ("every Monday at 10 AM") into structured `ScheduledTask` objects.
- **SQLite Persistence**: Stores task definitions and run execution records in `scheduled_tasks` and `task_runs` tables using `DatabaseManager`.
- **Orchestrator Execution Pipeline**: All scheduled tasks execute through `JarvisOrchestrator` -> `PlanExecutor`. The scheduler never directly executes arbitrary commands or bypasses security policies.
- **Runtime Permission Evaluation**: Evaluates security permissions at task execution time using `PermissionEvaluator`. High-risk tasks enter `WAITING_FOR_CONFIRMATION` if unauthorized.
- **Event-Driven Wait Loop**: `TaskScheduler` thread sleeps on a condition wake event until the exact timestamp `next_run_at`, consuming 0.0% CPU when idle.
- **Notification Manager**: Multi-channel delivery (Text -> Desktop -> Voice fallback).
- **Prompt 015 Self-Recovery**: Automatically invokes `JarvisRecoveryManager` on execution failure; auto-pauses tasks after 3 consecutive failures.
- **10 Tools & 6 Builtin Skills**: Full set of `scheduler.*` tools and skills (`schedule_task`, `cancel_task`, `list_tasks`, `pause_task`, `resume_task`, `task_history`).
