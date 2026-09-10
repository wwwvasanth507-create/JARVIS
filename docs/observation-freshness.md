# Observation Freshness & Pre-Action Re-Observation

## Observation Cache (`src/jarvis/core/orchestration/observation_cache.py`)
Enforces bounded TTL caching for observations.

### Pre-Action Re-Observation Rules:
- Before executing critical side-effect tools (`delete`, `submit`, `close`, `upload`), `ObservationCache.requires_reobservation()` requires fresh state inspection to prevent acting on stale observations.
