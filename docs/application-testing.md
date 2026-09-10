# Application Subsystem Testing Strategy

Application testing is strictly partitioned into unit alias/safety tests and harmless integration lifecycle tests.

## Test Suites

1. **Unit Tests (`tests/unit/applications/`)**:
   - `test_registry_aliases.py`: Application registry loading, natural alias resolution, ambiguity detection.
   - `test_discovery_cache.py`: Native application discovery and index cache reading/writing.
   - `test_launcher_controller.py`: URL association, launcher validation, non-running health checks.
   - `test_safety_permissions.py`: Protected security software guarding and unsaved work detection.
   - `test_application_tools.py`: Tool registry integration and `BaseTool` wrappers.

2. **Integration Test (`tests/integration/applications/test_application_integration.py`)**:
   - Executes an 8-step lifecycle test using the harmless Calculator utility (`calc.exe`).
   - Verifies discovery, alias resolution, launching, process inspection, window focusing, health checking, graceful closing, and process termination verification.
