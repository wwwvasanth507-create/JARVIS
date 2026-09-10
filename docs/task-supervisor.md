# Task Supervisor Engine & Stall Detection

## Task Supervisor (`src/jarvis/core/tasks/supervisor.py`)
Provides periodic, lightweight supervisory checks over active tasks without waking CPU unnecessarily.

### Key Capabilities:
- **Stall Detection (`src/jarvis/core/tasks/stall_detector.py`)**: Detects frozen browser sessions, unresponsive apps, un-progressing workflows, and missing worker leases. Transitions stalled tasks to `RECOVERING` or `DEGRADED`.
- **Startup Reconciliation**: Scans for orphaned `RUNNING` tasks after crash or restart and safely transitions them to `PAUSED` without replaying irreversible side-effects.
