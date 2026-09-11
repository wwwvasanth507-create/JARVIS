# JARVIS Objective & Hierarchy Specification

## Goal Hierarchy
JARVIS enforces a strictly bounded 5-level operational hierarchy:
```text
Goal
 └── Objective
      └── Task
           └── Workflow
                └── Step
```

## Objective Dependencies & Cycle Prevention
Objectives within a goal support explicit directed acyclic graph (DAG) dependencies.
Before creating or updating objectives, `GoalPolicy.detect_objective_cycles()` traverses the dependency graph using depth-first search (DFS) to prevent circular references.

## Objective Statuses
- `PENDING`: Awaiting dependency completion.
- `IN_PROGRESS`: Currently executing step workflows.
- `BLOCKED`: Waiting for resource lease, file availability, or Boss input.
- `COMPLETED`: Verified post-conditions satisfied.
- `FAILED`: Execution or verification failed after recovery attempts.
- `SKIPPED`: Safely bypassed due to plan adaptation.
