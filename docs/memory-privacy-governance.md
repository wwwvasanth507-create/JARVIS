# Memory Privacy, Governance & Management

## Overview
JARVIS provides comprehensive memory governance features, empowering the Boss to inspect, search, explain, forget, export, and import all personal memory and knowledge graph items.

## User-Facing Memory Tools
1. `memory.list`: List stored memories filtered by category or scope.
2. `memory.search`: Search memories using keyword queries.
3. `memory.get`: Retrieve a specific memory item by key or ID.
4. `memory.forget`: Explicitly forget a preference, memory item, or entire category.
5. `memory.explain`: Provide source provenance, confidence, recency, and explanation for why a memory exists.
6. `memory.export`: Export stored memories and graph database to a local JSON file (`jarvis --export-memory`).
7. `memory.import`: Safely import external memory JSON backups with validation and deduplication (`jarvis --import-memory`).

## User Corrections
Supports natural language correction handling:
- `"Remember I prefer Firefox"` -> Stores explicit global or project preference.
- `"That's wrong"` -> Invalidates or reduces confidence of recent inferences.
- `"Forget my project settings"` -> Safely deletes matching memory scope.

## Integrity & Maintenance
Maintenance operations (`jarvis --memory-maintenance` or `MemoryMaintenanceManager`) verify database integrity, prune expired working context, rebuild indexes, and compact summaries.
