# Root-Cause Analysis Model

## Confidence Classification
- **LIKELY**: Empirical evidence strongly supports the diagnosed cause (e.g. `os.path.exists()` returned `False`).
- **POSSIBLE**: Symptom matches common patterns but empirical proof is incomplete.
- **UNKNOWN**: Error cannot be categorized with certainty; requires human intervention.

## Failure Categories
- `NOT_FOUND` / `PATH_INVALID`
- `AMBIGUOUS`
- `PERMISSION_DENIED`
- `TIMEOUT`
- `NETWORK_ERROR`
- `APPLICATION_NOT_READY`
- `VISUAL_TARGET_NOT_FOUND`
- `VERIFICATION_FAILED`
- `RESOURCE_UNAVAILABLE`
