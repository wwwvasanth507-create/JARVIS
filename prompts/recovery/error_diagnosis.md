# Error Diagnosis Guidelines

Rules for failure analysis and root cause determination:
1. **Empirical Evidence**: Base diagnosis strictly on actual error codes, stack traces, and UI observations.
2. **Failure Classification**: Categorize failures (TOOL_ERROR, TIMEOUT, PERMISSION_DENIED, MISSING_ELEMENT, STALL).
3. **Loop Protection**: Track attempt counts to prevent repeating failed actions.
4. **Human Handoff**: Escalate to the Boss when user input or credential entry is required.
