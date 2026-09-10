# JARVIS Self-Recovery, Diagnostics & Replanning

## Overview
The Self-Recovery subsystem (`src/jarvis/core/recovery/`) upgrades JARVIS's orchestration recovery mechanism from simple retries into a structured diagnostic, root-cause analysis, and security-governed replanning engine.

## Core Features
- **Deterministic Diagnostics First**: Fast, lightweight subsystem diagnostic checks before invoking local LLM reasoning.
- **Extensible Failure Taxonomy**: Standardized classification into categories (`NOT_FOUND`, `AMBIGUOUS`, `PERMISSION_DENIED`, `TIMEOUT`, `APPLICATION_NOT_READY`, `VISUAL_TARGET_NOT_FOUND`, `VERIFICATION_FAILED`, etc.).
- **Structured Root-Cause Analysis**: `RootCause` with confidence scoring (`LIKELY`, `POSSIBLE`, `UNKNOWN`) and domain-specific evidence (`DiagnosticEvidence`).
- **Targeted Recovery Strategies**: Pre-registered strategies (`RETRY_ONCE`, `REFRESH_STATE`, `REFRESH_APPLICATION_REGISTRY`, `RELOAD_BROWSER_PAGE`, `REQUERY_FILESYSTEM`, `REBUILD_PLAN`, `REQUEST_USER`).
- **Strict Permission Re-Check**: Every recovery action is re-evaluated by `PermissionEvaluator`. Recovery actions do not inherit implicit authorization.
- **Human Intervention Protocol**: Raises `HumanInterventionRequiredError` for HIGH/CRITICAL risk escalation, low confidence, or policy restrictions.
- **Loop Protection**: Detects 3 identical consecutive failures and raises `RecoveryLoopDetectedError`.
- **Bounded Budget**: Enforces limits via `RecoveryLimits` (`max_diagnostic_steps: 3`, `max_recovery_steps: 3`, `max_replans: 2`, `max_total_recovery_time: 60s`).
