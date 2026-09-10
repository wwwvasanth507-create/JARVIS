# JARVIS Subsystem Task Scheduling & Background Automation Audit

## Overview
This document audits existing background processing, job tracking, task queues, database persistence, and notification mechanisms across JARVIS subsystems prior to implementing **Prompt 016: Task Scheduling & Background Automation**.

---

## Subsystem Audit Matrix

| Subsystem | Feature | Implemented | Partial | Missing | Duplicate | Notes |
|---|---|---|---|---|---|---|
| **System** | In-Memory Task Queue | ✓ | | | | `TaskQueue` in `src/jarvis/system/task_queue.py` using `heapq` priority min-heap. |
| **Shell** | Background Jobs | ✓ | | | | `ShellJob` and `ShellExecutor.start_background_job` for async terminal processes. |
| **Memory / Database** | SQLite Connection & WAL | ✓ | | | | `DatabaseManager` in `src/jarvis/memory/database.py` with WAL mode and thread-safe connections. |
| **Voice / TTS** | Neural Speech Synthesis | ✓ | | | | `TTSEngine` and `VoiceManager.speak()` for voice output. |
| **Orchestration** | Goal Resolution & Execution | ✓ | | | | `JarvisOrchestrator` and `PlanExecutor` handling validated execution pipelines. |
| **Recovery** | Diagnostics & Replanning | ✓ | | | | `JarvisRecoveryManager` providing failure classification, diagnostic evidence, and strategy execution. |
| **Scheduler Core** | Persistent Task Scheduler | | | ✓ | | No persistent cron/timer scheduler (`ScheduledTask`, `TaskRun`). |
| **Scheduler Core** | Natural Language Schedule Parser | | | ✓ | | No schedule parser converting "in 30 mins" or "every Monday at 9 AM". |
| **Scheduler Core** | Missed Task & Overlap Policies | | | ✓ | | No missed-task or task-concurrency overlap enforcement. |
| **Scheduler Core** | Notification Manager | | | ✓ | | No unified `NotificationManager` handling text, desktop, and voice fallbacks. |
| **Scheduler Core** | Scheduler Toolset & Builtin Skills | | | ✓ | | No `scheduler.*` tools or `schedule_task`, `cancel_task` skills. |

---

## Detailed Status Analysis

### Implemented Subsystems
1. **In-Memory Task Queue**: `TaskQueue` (`src/jarvis/system/task_queue.py`) provides priority-based `TaskItem` management.
2. **Background Shell Execution**: `ShellJob` handles background process execution and tracking.
3. **Database Architecture**: `DatabaseManager` (`src/jarvis/memory/database.py`) provides SQLite WAL connections and schema script execution.
4. **Voice Output**: `VoiceManager` and `TTSEngine` provide text-to-speech rendering.

### Missing Subsystems
1. **Scheduler Package (`src/jarvis/scheduler/`)**:
   - `ScheduledTask`, `TaskRun`, `TaskStatus`, `RecurrencePattern`.
   - `ScheduleParser`: Deterministic & LLM-assisted schedule expression resolution.
   - `TaskPersistence`: SQLite storage for `scheduled_tasks` and `task_runs` tables using `DatabaseManager`.
   - `TaskScheduler` Loop: Negligible CPU wait-until-next-event loop.
   - `WorkerPool`: Bounded async worker queue (`max_concurrent_tasks: 2`, `max_queue_size: 50`).
   - `NotificationManager`: Unified notification delivery (Text -> Desktop -> Voice fallback).
   - `SchedulerPolicy` & Security: Runtime permission re-checks, missed task handling (`skip`, `run_once`), overlap policy (`skip`), and recurring failure auto-pausing.
   - `SchedulerTools`: 10 tools (`scheduler.create`, `scheduler.list`, `scheduler.get`, `scheduler.update`, `scheduler.delete`, `scheduler.cancel`, `scheduler.pause`, `scheduler.resume`, `scheduler.next_run`, `scheduler.history`, `scheduler.status`).
   - Builtin Skills: `schedule_task`, `cancel_task`, `list_tasks`, `pause_task`, `resume_task`, `task_history`.

---

## Integration Plan
The new subpackage `src/jarvis/scheduler/` will integrate with `DatabaseManager`, dispatch scheduled tasks through `JarvisOrchestrator`, re-check permissions via `PermissionEvaluator`, reuse `JarvisRecoveryManager` on failures, and provide `scheduler.*` tools and builtin skills.
