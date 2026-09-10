# JARVIS Release Gate & Validation Protocol

This document details the production release validation gate (`jarvis --release-check`) and packaging workflow.

---

## 1. Release Check Command

To verify if the codebase is ready for distribution, run:

```bash
jarvis --release-check
```

### Evaluated Criteria:
1. **Package Metadata**: Validates `pyproject.toml` version and structure.
2. **Core Runtime Imports**: Verifies all `jarvis.core` subpackages import cleanly.
3. **Desktop UI Imports**: Verifies `jarvis.ui` packages import cleanly.
4. **Configuration Validation**: Validates `config/config.yaml` against pydantic schema.
5. **Subsystem Doctor**: Runs 10 subsystem health checks (`JarvisDoctor`).
6. **Self-Test Suite**: Executes safe deterministic end-to-end self-test (`JarvisSelfTest`).
7. **Test Suite Discovery**: Ensures all pytest test modules exist and pass.

---

## 2. Release Decision Outcomes

- **`RELEASE READY`**: Exit code 0. All 7 release gate checks passed.
- **`RELEASE BLOCKED`**: Exit code 1. Reports exact blockers requiring resolution before release.

---

## 3. PyInstaller Executable Packaging

To build standalone `JARVIS.exe` for Windows:

```bash
pip install pyinstaller
pyinstaller installer/jarvis.spec
```

The resulting executable is generated under `dist/JARVIS/JARVIS.exe`.
