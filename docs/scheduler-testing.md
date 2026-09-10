# Task Scheduler Test Suite Documentation

## Test Categories
- **Unit Tests (`tests/unit/scheduler/`)**:
  - `test_schedule_parser.py`: Relative and recurring schedule parsing.
  - `test_task_persistence.py`: SQLite task and run CRUD operations.
  - `test_scheduler_policy.py`: Permission checks and failure threshold checks.
  - `test_scheduler_loop.py`: TaskScheduler start/stop/wake thread loop.
  - `test_scheduler_tools.py`: 8 `scheduler.*` tool execution tests.
- **Integration Tests (`tests/integration/scheduler/`)**:
  - `test_scheduler_integration.py`: End-to-end reminder dispatch and recurring failure auto-pausing.
