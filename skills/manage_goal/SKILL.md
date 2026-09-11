---
name: manage_goal
description: Create, activate, pause, resume, or cancel autonomous goals.
version: 1.0.0
author: JARVIS
intent_patterns:
  - "^(create|propose|activate|pause|resume|cancel)\\s+goal\\s+(.*)$"
  - "^manage\\s+goal\\s+(.*)$"
required_permissions:
  - SYSTEM_CONTROL
risk_level: MEDIUM
tools:
  - goal.create
  - goal.preview
  - goal.activate
  - goal.pause
  - goal.resume
  - goal.cancel
---

# Manage Goal Skill

Instructions for managing structured goal lifecycles in JARVIS:
1. **Creation & Proposal**: Generate structured goal proposals before activating complex background operations.
2. **Lifecycle Control**: Activate, pause, resume, or cancel goals safely based on Boss directives.
3. **Audit Trail**: Record state transitions in the event log.
