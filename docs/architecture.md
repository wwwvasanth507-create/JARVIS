# JARVIS Master Architecture Blueprint

> **System Architecture & Modular Component Specification**

---

## 1. System Vision & Design Principles

JARVIS is designed as an autonomous, local-first personal AI computer assistant. The core architectural principles are:

1. **Local Sovereignty**: Zero dependency on external AI cloud APIs (no OpenAI, no Anthropic, no Google AI keys) and zero dependency on Ollama. All intelligence runs directly on local hardware via optimized model providers (`llama.cpp` / GGUF).
2. **Primary Operator Control**: Built specifically for **The Boss**. Every action is evaluated against security permissions and risk tiers defined in `config/permissions.yaml`.
3. **Autonomous Closed Loop**: Action execution is always accompanied by observation and explicit state verification. JARVIS never assumes an action succeeded without empirical evidence.
4. **Strict Modular Decoupling**: Subsystems (voice, vision, browser control, filesystem, shell, memory) are exposed to the central planner strictly via standardized tool interfaces.

---

## 2. Master Conceptual Architecture

```text
                                  +-------------------+
                                  |    User (Boss)    |
                                  +---------+---------+
                                            |
                                            v
                                  +-------------------+
                                  | Interface (UI/CLI)|
                                  +---------+---------+
                                            |
                                            v
                                  +-------------------+
                                  | Speech/Text Proc. |
                                  +---------+---------+
                                            |
                                            v
                                  +-------------------+
                                  | Fast Intent Router|
                                  +---------+---------+
                                 /                     \
                      (Simple Command)             (Complex Goal)
                            /                           \
                           v                             v
               +-------------------+           +-------------------+
               | Direct Tool Exec. |           |   JARVIS Brain    | <---> [ LocalModelProvider ]
               +---------+---------+           +---------+---------+
                         |                               |
                         |                               v
                         |                     +-------------------+
                         |                     |  Context Manager  | <---> [ Knowledge Index ]
                         |                     +---------+---------+
                         |                               |
                         |                               v
                         |                     +-------------------+
                         |                     |      Planner      |
                         |                     +---------+---------+
                         |                               |
                         +---------------+---------------+
                                         |
                                         v
                               +-------------------+
                               | Security Layer    | <---> [ permissions.yaml ]
                               +---------+---------+
                                         |
                                         v
                               +-------------------+
                               | Tool Executor     | <---> [ Resource Manager ]
                               +---------+---------+
                                         |
               +-------------------------+-------------------------+
               |                         |                         |
               v                         v                         v
     +-------------------+     +-------------------+     +-------------------+
     | Computer & Vision |     | Browser Control   |     | Filesystem & OS   |
     +-------------------+     +-------------------+     +-------------------+
               |                         |                         |
               +-------------------------+-------------------------+
                                         |
                                         v
                               +-------------------+
                               |     Observer      |
                               +---------+---------+
                                         |
                                         v
                               +-------------------+
                               |     Verifier      |
                               +---------+---------+
                                         |
                                [ Validated State? ]
                                   /           \
                                (YES)          (NO)
                                 /               \
                                v                 v
                      +-------------------+  +-------------------+
                      | Response Generator|  |  Recovery Engine  |
                      +---------+---------+  +---------+---------+
                                |                      |
                                v                      +---> Re-Plan & Retry
                      +-------------------+
                      | Voice/Text Output |
                      +-------------------+
```

---

## 3. Subsystem Breakdown & Responsibilities

### 3.1 Interface Layer (`src/jarvis/ui/`)
- Manages user input channels (CLI terminal, floating desktop overlay, voice hotkey listeners).
- Formats final output responses for visual display and audio playback.

### 3.2 Speech & Text Processing (`src/jarvis/voice/`)
- **Speech-to-Text (STT)**: Converts spoken audio input from microphone into text (using local models like Whisper / Faster-Whisper CPU).
- **Wake-Word Listener**: Continuously listens for "JARVIS" wake-word with minimal CPU overhead.
- **Text-to-Speech (TTS)**: Synthesizes responses using local female TTS models (e.g. Piper TTS).

### 3.3 JARVIS Brain & Model Provider (`src/jarvis/brain/`)
- **`LocalModelProvider` Interface**: Abstract model wrapper decoupling the agent core from specific C++ runtimes (`llama.cpp`, GGUF bindings).
- **Prompt Formulation**: Injects identity system prompts (`prompts/identity/`), current context, user instructions, and active tool definitions into structured LLM prompts.

### 3.4 Context Manager & Memory (`src/jarvis/memory/`)
- **Short-Term Context**: Manages sliding conversation window and active task scratchpad.
- **Long-Term Memory**: Stores user preferences, previous interaction history, and knowledge embeddings in local SQLite / DuckDB / vector storage (`data/database/`).

### 3.5 Planner & Goal Decomposition (`src/jarvis/brain/loop.py`)
- Takes complex multi-step goals from the Boss and breaks them down into atomic, executable steps.
- Selects appropriate tools based on tool descriptions and schemas.

### 3.6 Security & Permission Layer (`src/jarvis/security/`)
- Intercepts every tool call before execution.
- Checks permission categories (`READ_FILES`, `WRITE_FILES`, `DELETE_FILES`, `RUN_COMMANDS`, `BROWSER_CONTROL`, `NETWORK_ACCESS`, `APPLICATION_CONTROL`, `SYSTEM_CONTROL`).
- Enforces risk policy levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). `HIGH` and `CRITICAL` risk actions require explicit Boss confirmation.

### 3.7 Tool Executor & Handlers (`src/jarvis/tools/`)
- Unified interface for executing tools:
  - `computer.*`: Mouse movement, clicking, typing, screenshot capture (`src/jarvis/computer/`).
  - `browser.*`: Navigation, element clicking, text extraction (`src/jarvis/browser/`).
  - `filesystem.*`: File searching, reading, writing, moving (`src/jarvis/filesystem/`).
  - `application.*`: Launching, focusing, closing applications (`src/jarvis/applications/`).
  - `shell.*`: Controlled command execution in sandboxed environments (`src/jarvis/shell/`).

### 3.8 Observer (`src/jarvis/observability/`)
- Captures system state immediately after tool execution (e.g. UI screenshots, process status, file metadata, command exit codes, HTTP response codes).

### 3.9 Verifier (`src/jarvis/brain/`)
- Evaluates empirical evidence from the Observer against expected step conditions.
- Examples:
  - *Clicking Play button*: Verifies audio output stream or UI pause icon change.
  - *Creating a file*: Verifies file exists on disk with non-zero byte size.

### 3.10 Recovery & Replanning Engine (`src/jarvis/brain/`)
- Triggered when state verification fails.
- Analyzes error message / visual discrepancy, updates context with failure details, and requests a corrected plan from the Planner.

---

## 4. Security Principles

1. **Least Privilege**: Tools operate under strict sandbox constraints.
2. **Explicit Authorization**: Destructive file deletions or arbitrary command execution require interactive approval from the Boss.
3. **Auditing**: All executed tools, parameters, results, and permission checks are logged to `logs/audit.log`.

---

*Architectural specification approved for JARVIS Phase 1.*
