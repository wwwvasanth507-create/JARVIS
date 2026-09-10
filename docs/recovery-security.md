# Recovery Security Architecture

## Mandatory Permission Re-Checks
Recovery steps execute under strict security oversight. Before dispatching any recovery action:
1. `PermissionEvaluator.evaluate()` is called on the recovery tool and parameters.
2. If authorization is denied, `RecoveryPermissionDeniedError` is raised.
3. If risk level escalates (e.g. LOW → HIGH), `HumanInterventionRequiredError` halts execution until confirmed by the Boss.

## Loop Protection
`JarvisRecoveryManager` tracks tool signature histories (`tool_name:sorted_args:error_message`). If 3 identical consecutive failures occur, `RecoveryLoopDetectedError` aborts execution to prevent resource exhaustion or infinite retry loops.
