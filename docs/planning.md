# Multi-Step Planning & Validation

The Planning subsystem (`src/jarvis/core/orchestration/planner.py`, `plan.py`, `policy.py`) constructs and validates structured execution plans.

---

## Plan Structure

Each `Plan` contains a list of `PlanStep` items:

* `step_id`: Unique identifier
* `description`: Human-readable summary
* `tool_name`: Target tool registered in tool registry
* `arguments`: Structured JSON parameters
* `dependencies`: List of preceding `step_id` dependencies
* `risk_level`: Assigned risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
* `permission`: Required permission category
* `status`: Step lifecycle state (`PENDING`, `WAITING_FOR_CONFIRMATION`, `EXECUTING`, `COMPLETED`, `FAILED`, `CANCELLED`, `SKIPPED`)

## Plan Quality Scoring (`PlanQualityScorer`)

`PlanQualityScorer.score_plan(plan)` evaluates multi-step plans before execution:
- Checks dependency completeness (missing dependencies deduct 0.3).
- Validates tool specificity (unspecified or generic tools deduct 0.2).
- Rejects plans with quality scores below 0.6.

---

## Dynamic Adaptation & Loop Defense

- **Observation-Based Adaptation**: Plans re-evaluate next steps based on runtime observations (e.g. focusing an already open browser rather than launching another instance).
- **Semantic Loop Defense**: `ObservationManager.detect_semantic_loop()` detects repeated identical or semantically duplicate tool invocations and triggers recovery before execution gets stuck.
