---
name: inspect_goals
description: List, get, and query active or historical goal details.
version: 1.0.0
author: JARVIS
intent_patterns:
  - "^(list|show|get|inspect)\\s+goals?\\s*(.*)$"
  - "^what\\s+goals\\s+are\\s+active\\??"
required_permissions:
  - SYSTEM_CONTROL
risk_level: LOW
tools:
  - goal.list
  - goal.get
---

# Inspect Goals Skill

Instructions for querying and displaying goal state details in JARVIS.
