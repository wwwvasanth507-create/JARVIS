# JARVIS Developer Guidelines & Standards

---

## 1. Code Quality & Formatting Rules

All Python code in **JARVIS** must adhere to the following standards:

1. **Python Version**: Python 3.10+ compatible code (tested on Python 3.14.7).
2. **Type Hints**: Modern Python typing syntax is **mandatory** for all function signatures, class attributes, and return values.
   ```python
   def evaluate_permission(category: str, risk_level: str) -> bool:
       ...
   ```
3. **Small Functions & Single Responsibility**: Functions should focus on a single operation and remain concise (under 50 lines per function where practical).
4. **Clean Module Boundaries**: No circular imports. Modules under `src/jarvis/` must communicate through public APIs or interfaces.
5. **No Swallowing Exceptions**: Never use bare `except:` or silent `pass` blocks. Always catch explicit exception types and log or propagate errors.
6. **No Global Mutable State**: State must be encapsulated in managed instances or configuration objects.
7. **Structured Logging**: Use Python's standard `logging` library or structured JSON loggers (`src/jarvis/observability/`). Do not use raw `print()` statements in core package code.

---

## 2. Project Layout Standards

```text
src/jarvis/
├── core/         # Bootstrap, settings loader, constants
├── brain/        # Model provider interfaces, agent loop, verification
├── security/     # Permission checks, risk policy engine
├── tools/        # Base tool interface and concrete tool registrations
├── observability/# Logging, tracing, and metric collection
└── ...
```

- Each module directory must contain an `__init__.py` exposing clean entry points.
- Core classes must be unit-testable in isolation without requiring external network connectivity or specialized hardware.

---

## 3. Configuration & Security Guidelines

1. **Externalized Settings**: Hardcoded magic numbers, file paths, or parameters in code are prohibited. All operational settings must be loaded from `config/config.yaml` or `config/permissions.yaml`.
2. **No Committed Secrets**: Never commit API tokens, credentials, or private user data.
3. **Risk Level Annotations**: Every tool created in `src/jarvis/tools/` must declare its risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and permission requirements.

---

## 4. Testing & Verification

1. **Unit Tests (`tests/unit/`)**: Verify individual functions, schema validation, configuration parsing, permission checking logic, and model provider abstractions.
2. **Integration Tests (`tests/integration/`)**: Test interaction between the Planner, Security layer, and Tool Executor using dummy tools.
3. **Agent Tests (`tests/agent/`)**: Test multi-step loop scenarios in controlled mock environments.
4. **Execution Command**:
   ```bash
   pytest tests/unit/
   ```

---

*JARVIS Developer Guide — Phase 1.*
