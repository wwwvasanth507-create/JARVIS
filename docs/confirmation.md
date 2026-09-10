# Confirmation Management

High and Critical risk actions (such as file deletion, shell execution, application closing with unsaved work) require user confirmation (`src/jarvis/core/orchestration/confirmation.py`).

---

## Confirmation Token Lifecycle

```text
Plan Step (HIGH/CRITICAL Risk)
         ↓
Generate PendingConfirmation (8-char unique token)
         ↓
State set to WAITING_FOR_CONFIRMATION
         ↓
Boss prompted with action description & confirmation token
         ↓
User responds with confirmation token
         ↓
Token validated & consumed (5-minute expiration)
         ↓
Plan Step executes
```

---

## Safety Rules

* Confirmations expire automatically after 300 seconds.
* Each confirmation token can only be consumed once.
* General affirmative words ("yes", "ok") without a matching pending token will NOT trigger execution.
