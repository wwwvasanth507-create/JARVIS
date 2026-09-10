# Scheduler Integration with Prompt 015 Recovery

## Closed-Loop Self-Recovery
When a scheduled task execution fails:
1. `TaskExecutor` captures the failure error message.
2. `SchedulerRecovery` invokes `JarvisRecoveryManager` diagnostics.
3. If recovery is possible and authorized, a `RecoveryPlan` is generated.
4. If a recurring task fails 3 consecutive times (`recurring_failure_threshold: 3`), `SchedulerPolicy` auto-pauses the task and alerts the Boss.
