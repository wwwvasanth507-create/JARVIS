# Conservative Proactive Context Engine

## Principles
JARVIS implements a conservative proactive context layer (`ProactiveContextEngine`).

### Permitted Proactive Behaviors:
- Surfacing requested scheduled reminders (`REMINDER`).
- Alerting the Boss when a background task fails (`TASK_FAILED`).
- Notifying when a requested condition monitor triggers (`TASK_COMPLETE`).

### Prohibited Proactive Behaviors:
- Spontaneously making financial transactions.
- Spontaneously sending external emails or messages.
- Spontaneously deleting local files or modifying permissions.
- Unrestricted background continuous LLM reasoning loops.
