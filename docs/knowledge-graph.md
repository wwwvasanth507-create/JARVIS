# Local Knowledge Graph Architecture

## Overview
JARVIS embeds an lightweight, SQLite-backed Knowledge Graph (`KnowledgeGraphManager`) for entity resolution, alias mapping, and relationship tracking across projects, applications, documents, and preferences.

## Schema

### Entities (`nodes`)
- `node_id`: Unique Identifier
- `entity_type`: `PERSON`, `PROJECT`, `APPLICATION`, `FILE`, `FOLDER`, `DOCUMENT`, `WEBSITE`, `TASK`, `PREFERENCE`, `DEVICE`, `LOCATION`, `ORGANIZATION`
- `name`: Primary Entity Name
- `aliases`: JSON List of Canonical & Informal Aliases (e.g. `["Chrome", "Google Chrome", "chrome.exe"]`)
- `properties`: JSON Attributes
- `source`: Provenance Tag
- `confidence`: Numeric Confidence Score (0.0 to 1.0)

### Relationships (`edges`)
- `edge_id`: Unique Edge Identifier
- `source_id`: Origin Node ID
- `target_id`: Target Node ID
- `relation_type`: `OWNS`, `USES`, `PREFERS`, `LOCATED_IN`, `CONTAINS`, `DEPENDS_ON`, `CREATED`, `MODIFIED`, `RELATED_TO`, `WORKS_ON`, `GENERATED`, `USED_IN`
- `weight`: Numeric Weight
- `properties`: Edge Attributes

## Bounded Traversal Limits
Graph traversals are strictly bounded to prevent CPU loops:
- `max_depth` <= 3
- `max_nodes` <= 50

## Graph Poisoning Defense
External/untrusted web content is marked with `EXTERNAL_CONTENT` trust source (0.3) and cannot automatically create trusted edges or high-confidence nodes without explicit user confirmation.
