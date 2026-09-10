# Recovery Subsystem Architecture

## Workflow Diagram
```
Action
 ↓
Observation
 ↓
Verification → Failure
                 ↓
            Diagnostics (DiagnosticEngine)
                 ↓
            Root-Cause Classification (FailureClassifier)
                 ↓
            Recovery Strategy (StrategyRegistry)
                 ↓
            Permission Re-Check (RecoveryPolicy / PermissionEvaluator)
                 ↓
            Recovery Action / Replan / Human Intervention
                 ↓
            Verification → Success / Safe Failure / Loop Detected
```

## Key Components
- `JarvisRecoveryManager`: Central coordinator.
- `FailureClassifier`: Maps failure events to failure categories.
- `DiagnosticEngine`: Collects deterministic evidence (`DiagnosticEvidence`).
- `RecoveryPlanner`: Generates `RecoveryPlan`.
- `RecoveryExecutor`: Dispatches recovery steps with security checks.
- `DiagnosticReplanner`: Rebuilds goal plans using diagnostic findings.
- `RecoveryPolicy`: Evaluates authorization, confidence levels, and risk escalation.
