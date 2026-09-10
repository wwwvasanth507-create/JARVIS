# Scheduler SQLite Persistence & Migrations

## Database Integration
The scheduler uses the project's shared SQLite database (`data/database/memory.db`) managed via `DatabaseManager`.

## Database Schema
### Table: `scheduled_tasks`
- `task_id` (TEXT PRIMARY KEY)
- `name` (TEXT)
- `description` (TEXT)
- `action` (TEXT)
- `skill_id` (TEXT)
- `tool_name` (TEXT)
- `arguments` (JSON TEXT)
- `schedule` (TEXT)
- `timezone` (TEXT)
- `status` (TEXT)
- `priority` (INTEGER)
- `risk_level` (TEXT)
- `enabled` (INTEGER)
- `created_at` (REAL)
- `updated_at` (REAL)
- `next_run_at` (REAL)
- `last_run_at` (REAL)
- `last_result` (JSON TEXT)
- `failure_count` (INTEGER)
- `is_recurring` (INTEGER)
- `notification_type` (TEXT)

### Table: `task_runs`
- `run_id` (TEXT PRIMARY KEY)
- `task_id` (TEXT FOREIGN KEY)
- `started_at` (REAL)
- `finished_at` (REAL)
- `status` (TEXT)
- `result` (JSON TEXT)
- `error` (TEXT)
- `verification_result` (JSON TEXT)
- `recovery_attempts` (INTEGER)
