# JARVIS Subsystem Recovery & Diagnostics Audit

## Overview
This document audits existing error handling, verification, retry, loop detection, and state recovery implementations across JARVIS subsystems prior to implementing **Prompt 015: Self-Recovery, Diagnostics & Intelligent Replanning**.

---

## Subsystem Audit Matrix

| Subsystem | Feature | Implemented | Partial | Missing | Duplicated | Notes |
|---|---|---|---|---|---|---|
| **Orchestration** | Step Retries | ✓ | | | | `RecoveryManager.can_retry_step` (max 1 retry for LOW/MEDIUM risk). |
| **Orchestration** | Replanning | | ✓ | | | Basic replan counter in `RecoveryManager`; no intelligent replan generator. |
| **Orchestration** | Loop Detection | ✓ | | | | `RecoveryManager.track_action` detects 3 identical consecutive failures. |
| **Orchestration** | Diagnostics & Root Cause | | | ✓ | | No structured diagnostic engine or failure classification. |
| **Brain / LLM** | Fallback / Model Retry | ✓ | | | | `LlamaCppModelProvider` / `MockModelProvider` fallback; no auto model reset. |
| **Applications** | Process & Window Polling | ✓ | | | | Application readiness polling and window focus verification in launcher. |
| **Browser** | Navigation Verification | ✓ | | | | URL and DOM readiness checks in Playwright controller. |
| **Filesystem** | Path Safety & Atomic Edits | ✓ | | | | `PathSafetyEvaluator` and atomic backup file writers. |
| **Shell** | Command Execution & Timeouts | ✓ | | | | Subprocess timeout handling, background job tracking, exit code capture. |
| **Vision / Screen** | Screen State Comparison | ✓ | | | | `ScreenComparator` dHash diffs, `VisualStateVerifier` for post-condition checks. |
| **Security** | Permission Evaluator | ✓ | | | | Category & risk checks; no permission re-check on recovery actions. |

---

## Detailed Status Analysis

### Implemented Subsystems
1. **Bounded Step Retries**: `PlanExecutor` retries low/medium-risk failed steps once using `RecoveryManager.can_retry_step`.
2. **Execution Loop Prevention**: `RecoveryManager` tracks tool signature histories (`tool:args:error`) and raises `LoopDetectedError` if identical failures repeat 3 times.
3. **Subsystem Post-Condition Verification**: `VerificationManager`, `VisualStateVerifier`, browser DOM checks, and process health checks verify step execution.

### Partial Subsystems
1. **Replanning Architecture**: `RecoveryManager` maintains `replan_count` and `max_replans`, but `JarvisOrchestrator` lacks automated diagnostic-driven replan loops.

### Missing Subsystems
1. **Diagnostic Engine & Failure Taxonomy**: No `FailureEvent` classification or root-cause analyzer (`RootCause`).
2. **Recovery Strategy Planner**: No `RecoveryPlanner` or `RecoveryStrategy` mapping failure root-causes to targeted recovery steps (e.g. refreshing window registry, re-querying DOM, searching alternate paths).
3. **Permission Re-Evaluation on Recovery**: Recovery actions do not currently undergo mandatory `PermissionEvaluator` re-checking.
4. **Human Intervention Protocol**: No formal `HumanInterventionRequired` exception and prompt structure for ambiguous or high-risk recovery scenarios.
5. **Recovery Audit Log & Benchmark**: No dedicated recovery event metrics (`data/cache/recovery-benchmark.json`).

---

## Integration Plan
The new subpackage `src/jarvis/core/recovery/` will extend `src/jarvis/core/orchestration/recovery.py`, seamlessly integrating with `PlanExecutor` and `JarvisOrchestrator` without breaking existing verification or permission systems.
