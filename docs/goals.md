# JARVIS Goal Subsystem Architecture

## Overview
The Goal Subsystem provides governed, multi-step goal management for **JARVIS**. Rather than treating every user interaction as an isolated command, JARVIS maintains structured goals, objectives, priority scheduling, resource arbitration, autonomy levels (0–3), checkpoints, and failure recovery over time.

## Architecture
```text
User Intent (Boss)
  ↓
Goal Proposal / Intent Resolver
  ↓
GoalManager (src/jarvis/core/goals/manager.py)
  ↓
GoalPolicy (Autonomy Levels 0-3, Security & Depth Bounds)
  ↓
BoundedGoalPriorityQueue (Starvation Protection & User Override)
  ↓
GoalArbitrator (Resource Lease & Dependency Checks)
  ↓
WorkflowEngine / JarvisOrchestrator
  ↓
Verification & Checkpoints (SQLite V2)
  ↓
Strategy Memory & Outcome Postmortem
```

## Core Models
- **Goal**: Top-level entity representing user objective (`DRAFT`, `ACTIVE`, `PAUSED`, `BLOCKED`, `WAITING_FOR_USER`, `AT_RISK`, `COMPLETED`, `PARTIAL_SUCCESS`, `FAILED`, `CANCELLED`, `EXPIRED`).
- **Objective**: Structured sub-task within a goal with dependencies and completion criteria.
- **GoalCheckpoint**: State snapshot storing verified outputs, blockers, and resource usage.
- **GoalProgress**: Calculated progress percentage, confidence level, deadline risk, and explainable health score.
