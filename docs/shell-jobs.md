# Background Shell Job Management

JARVIS manages long-running terminal commands asynchronously through structured `ShellJob` handles to prevent blocking the agent or UI threads.

## Job Lifecycle

```
QUEUED ──► RUNNING ──► COMPLETED (exit_code == 0)
              │
              ├──► FAILED (exit_code != 0)
              │
              ├──► TIMED_OUT (exceeds timeout limit)
              │
              └──► CANCELLED (via `shell.cancel`)
```

## Management Features

- `shell.execute` with `is_background=True` launches execution in a background thread and returns a `ShellJob` object with a unique `job_id`.
- `shell.job_status`: Inspects job state (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `TIMED_OUT`, `CANCELLED`) and duration.
- `shell.job_output`: Retrieves stdout/stderr logs capped by byte and line limits.
- `shell.cancel`: Terminates active process trees gracefully using `JobCanceller`.
- Concurrency limit (`max_concurrent_jobs: 5`) prevents process resource exhaustion.
