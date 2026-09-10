# JARVIS Memory Context & Conflict Resolution

## Memory Usage 2.0
- Memory retrieval (`MemoryRetriever`) performs entity-aware, project-aware, bounded contextual queries instead of dumping the entire SQLite database into context.

## Memory Write Policy
- Permanent memory persistence is restricted to verified user preferences (e.g. Tamil response preference, preferred browser) and long-term project configuration.
- Potential secrets, transient scratch paths, and temporary conversation tokens remain blocked.

## Memory Conflict Resolution
- When contradictory facts or preferences exist (e.g., Old preference: Chrome, New preference: Firefox), newer facts supersede older facts based on timestamp ordering.
