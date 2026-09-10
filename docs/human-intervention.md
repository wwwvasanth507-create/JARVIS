# Human Intervention Protocol

## Triggers for Human Intervention
- High/Critical risk recovery strategies.
- Low or UNKNOWN root-cause confidence.
- `PERMISSION_DENIED` or `AMBIGUOUS` failure categories.
- High-risk escalation (LOW → HIGH).

## Exception Interface
When intervention is required, JARVIS raises `HumanInterventionRequiredError` providing:
- `reason`: Why intervention is required.
- `blocked_action`: The action that was stopped.
- `evidence`: Diagnostic evidence summary.
- `safe_next_action`: Suggested safe choice for the Boss.
