# Goal Memory & Checkpoints

Goal state and objective checkpoints are persisted in SQLite V2 (`goals`, `objectives`, `goal_checkpoints`, `goal_logs`).

## Provenance & Integrity
- Checkpoints store verified outputs, active blockers, and resource metrics.
- Post-restart startup reconciliation (`reconcile_goals_on_startup()`) re-validates permissions and environment before resuming active goals.
- Goals log events into `goal_logs` and publish system events on the `JarvisEventBus`.
