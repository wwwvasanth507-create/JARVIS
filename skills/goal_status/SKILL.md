---
name: goal_status
description: Calculate and explain goal progress, health scores, and blockers.
version: 1.0.0
author: JARVIS
intent_patterns:
  - "^(explain|progress|status\\s+of)\\s+goal\\s+(.*)$"
  - "^how\\s+is\\s+goal\\s+(.*)\\s+doing\\??"
required_permissions:
  - SYSTEM_CONTROL
risk_level: LOW
tools:
  - goal.progress
  - goal.explain
---

# Goal Status Skill

Instructions for calculating and reporting progress percentage, confidence level, health score, and blockers for any goal.
