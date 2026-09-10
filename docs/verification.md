# Verification & Observation Subsystem

JARVIS enforces strict state verification (`src/jarvis/core/orchestration/verification.py`). Success is never reported merely because an API or process invocation returned without raising an exception.

---

## Verification Strategies per Subsystem

| Subsystem | Verification Method | Post-Condition Verified |
|---|---|---|
| **Application** | Process & Window Check | Target PID running AND active window present |
| **Filesystem** | File System Inspection | File/directory existence, hash check, path within allowed root |
| **Browser** | Navigation Audit | Target URL loaded AND page text accessible |
| **Shell** | Exit Code & Stream Audit | Exit code == 0 AND expected output streams matched |
| **Computer** | Window Manager Inspection | Focus verified on OS window list |

---

## Mandatory Rule

If post-condition verification fails, `VerificationManager` returns `verified = False` and sets step state to `FAILED`. JARVIS reports truthful failure rather than hallucinating success.
