# Scheduler Security & Permission Model

## Runtime Permission Re-Evaluation
Permissions are evaluated at task execution time using `PermissionEvaluator`. A task created on Monday re-evaluates permissions when executing on Friday.

## Risk Handling & Authorization
- High/Critical risk tasks require confirmation and enter `WAITING_FOR_CONFIRMATION` if unauthorized.
- Missed high-risk tasks while JARVIS was offline do NOT auto-execute; `missed_task_policy: skip` skips them safely.
- Scheduled tasks cannot bypass permissions or execute arbitrary Python code.
