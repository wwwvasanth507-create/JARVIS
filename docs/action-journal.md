# Action Journal & Task Replay

## Action Journal (`src/jarvis/observability/action_journal.py`)
User-facing log recording recent assistant tool executions, workflow events, automations, and condition triggers.

## Secret Redaction & Replay Safety
- Automatically redacts passwords, tokens, API keys, and Base64 secrets from summary strings and details dictionaries.
- `system.replay_task` allows replaying structured logged operations after re-evaluating permissions against active context.
