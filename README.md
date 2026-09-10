# JARVIS — Local Personal AI Assistant

> **"At your service, Boss."**

**JARVIS** is a local-first personal AI computer agent designed to run directly on the user's computer. It operates with full local sovereignty, providing voice and chat interaction, autonomous goal planning, computer and browser control, filesystem management, shell execution, multi-step task resolution, and continuous verification.

---

## Key Principles & Philosophy

- **Local-First & Autonomous**: Executes locally on user hardware. Designed to operate without external cloud AI APIs (no OpenAI, no Anthropic, no Google AI keys required).
- **No Ollama Dependency**: Employs direct local model provider abstractions targeting native local inference runtimes such as `llama.cpp` (GGUF).
- **Primary Operator Sovereignty**: Addresses the primary user as **Boss** and respects explicit security boundaries and permission controls.
- **Modular & Extensible**: Architected with strict decoupling across core modules, security evaluators, tool execution layers, and memory providers.
- **Observable & Verifiable**: Every action follows an autonomous loop (*Understand → Plan → Check Permissions → Execute → Observe → Verify → Recover*) that verifies state changes before declaring success.

---

## Master Architecture Overview

```text
User (Boss)
  ↓
Interface (Voice / Chat UI)
  ↓
Speech & Text Processing
  ↓
JARVIS Brain (LocalModelProvider)
  ↓
Context Manager & Memory
  ↓
Planner & Task Resolver
  ↓
Security & Permission Layer (permissions.yaml)
  ↓
Tool Executor
  ↓
Subsystems (Computer | Browser | Filesystem | Applications | Shell)
  ↓
Observer (Screen & Output Analysis)
  ↓
Verifier (State Verification)
  ↓
Recovery & Replanning engine
  ↓
Response (Audio / Text Output)
```

---

## Directory Structure

```text
JARVIS/
├── README.md                 # Project Overview & Architecture Guide
├── pyproject.toml             # Python Package Metadata & Dependencies
├── .gitignore                # Git Exclusions
├── LICENSE                   # MIT License
│
├── docs/                     # Comprehensive Project Documentation
│   ├── architecture.md       # Master Architecture Blueprint
│   ├── environment.md        # Empirical Hardware & System Report
│   ├── development.md        # Developer Guidelines & Code Standards
│   ├── roadmap.md            # 20-Phase Master Development Roadmap
│   └── knowledge-architecture.md # 10,000+ Markdown Scaling Strategy
│
├── config/                   # System Configuration & Security Rules
│   ├── config.yaml           # Core System & Model Settings
│   ├── permissions.yaml      # Security Categories & Risk Levels
│   └── applications.yaml     # Application Registry Rules
│
├── src/                      # Source Code Core
│   └── jarvis/
│       ├── core/             # Configuration & Bootstrap
│       ├── brain/            # Model Provider & Agent Loop
│       ├── voice/            # Speech Recognition & Synthesis
│       ├── computer/         # Screen & Input Automation
│       ├── browser/          # Web Browser Control
│       ├── filesystem/       # File Operations
│       ├── shell/            # Shell Command Execution
│       ├── applications/     # Application Controllers
│       ├── memory/           # Database & Vector Memory
│       ├── security/         # Permission Evaluator
│       ├── skills/           # Dynamic Skill Loader
│       ├── tools/            # Tool Base Class & Definitions
│       ├── observability/    # Logging & Tracing
│       └── ui/               # Interface Components
│
├── prompts/                  # System & Agent Prompt Definitions
│   └── identity/             # Identity, Personality & Relationship
├── knowledge/                # Indexed Knowledge Artifacts
├── skills/                   # Modular Skill Definitions
├── tests/                    # Modular Test Suite (Unit, Integration, Agent, Eval)
├── data/                     # Local Database, Cache, and Memory Storage
├── logs/                     # Application & Execution Logs
└── scripts/                  # Operational Scripts
```

---

## Current Development Stage

**Phase 1: Project Foundation & Core Subsystems**

- Environment inspected and hardware budget established.
- Core package structure initialized.
- Modular architecture and autonomous loop documented.
- Security permission system and risk tiers defined.
- Tool abstractions and local model provider interfaces established.
- Master 20-phase roadmap defined.
- CPU-first local AI inference, chat, voice, wake-word, computer control, and browser automation established.
- **Prompt 007 Completed**: Fully integrated Filesystem & File Management Layer (`src/jarvis/filesystem/`) with path safety, 16 structured tools, permission policy checks, atomic writes, targeted edits, multi-criteria search, staged duplicate detection, file organization, storage reporting, and verified integration testing.
- **Prompt 008 Completed**: Fully integrated Controlled Shell & Terminal Layer (`src/jarvis/shell/`) with 9 structured tools, command parsing, dangerous operation blocking, zero autonomous privilege escalation, environment secret redaction, output capping, background `ShellJob` handles, process management, and audit logging.
- **Prompt 009 Completed**: Fully integrated Application Control & System Integration Layer (`src/jarvis/applications/`) with 12 structured tools, OS discovery, alias & ambiguity resolution, cache indexing (`data/indexes/applications.json`), graceful closing with unsaved-work guarding, window focus integration, readiness polling, and health checking.
- **Prompt 010 Completed**: Fully integrated Intent Understanding, Planning & Tool Orchestration Layer (`src/jarvis/core/orchestration/`) with fast-path parsing, goal resolution, plan generation & static validation, security policy enforcement, tokenized confirmation handling, post-condition verification, bounded recovery, and real-time cancellation.
- **Prompt 011 Completed**: Fully integrated Persistent Memory & Knowledge Architecture (`src/jarvis/memory/`) with SQLite storage (`data/database/memory.db`), explicit memory categories, pattern-matched privacy policy blocking credential storage, conflict deduplication, incremental Markdown knowledge indexing (SHA256), multi-signal ranking, and context builder.
- **Prompt 012 Completed**: Fully integrated Modular Skill & Capability System (`src/jarvis/skills/`) with declarative YAML manifests (`skills/`), skill discovery, validation, intent resolution, permission intersection, effective risk escalation, 5 builtin skills (`open_application`, `find_file`, `open_file`, `web_search`, `system_status`), and 6 skill management tools (`skill.list`, `skill.find`, `skill.info`, `skill.enable`, `skill.disable`, `skill.status`).
- **Prompt 013 (Document Processing) Completed**: Fully integrated Document Intelligence & Local Document Processing (`src/jarvis/documents/`) with format detection, deterministic & structural extractors (`.txt`, `.md`, `.json`, `.yaml`, `.csv`, `.html`, `.xml`, `.pdf`, `.docx`), text normalization, structural chunking, table extraction, document summarization, QA with grounded citations, document comparison diffs, atomic document creation, format conversion, `DocumentSecurityPolicy` prompt injection defense, and 10 document tools.
- **Prompt 013 (Production Model Runtime) Completed**: Fully integrated Production Local Model Runtime (`src/jarvis/brain/`) with direct `llama.cpp` GGUF local CPU execution (`n_gpu_layers=0`), RAM safety checks (`ModelMemoryChecker`), hardware-aware profiles (`config/models.yaml`), multi-directory model discovery (`models/language/`, `models/gguf/`), token streaming, cancellation, context window prioritization, structured tool-call parsing (`StructuredToolParser`), performance benchmarking (`data/cache/model-benchmark.json`), and graceful missing-model fallback mode.
- **Prompt 014 Completed**: Fully integrated Local Screen Understanding, OCR & Vision Layer (`src/jarvis/computer/vision/`).
- **Prompt 015 Completed**: Fully integrated Self-Recovery, Diagnostics & Intelligent Replanning (`src/jarvis/core/recovery/`).
- **Prompt 016 Completed**: Fully integrated Task Scheduling & Background Automation (`src/jarvis/scheduler/`).
- **Prompt 017 Completed**: Fully integrated Production Hardening, Real End-to-End Runtime & Distribution (`src/jarvis/app.py`, `src/jarvis/__main__.py`) with explicit application lifecycle (`ApplicationLifecycle`), hardware-aware performance modes (`ULTRA_LOW` through `GPU_ACCELERATED`), capability registry (`CapabilityRegistry`), CLI diagnostic tool (`jarvis --doctor`), self-test suite (`jarvis --self-test`), performance benchmark suite (`PerformanceBenchmark`), Windows batch and PowerShell launchers (`start_jarvis.bat`, `start_jarvis.ps1`), explicit user-controlled autostart manager (`AutostartManager`), end-to-end integration test suite, false-success defense, production readiness documentation (`docs/production-readiness.md`).
- **Prompt 018 Completed**: Fully integrated Production Desktop UI, System Tray & Unified Runtime (`src/jarvis/ui/`) with dark theme styling, glassmorphism UI elements, system tray integration, reactive task state visualization, audio visualizer, hotkey listeners, and notification dispatch.
- **Prompt 019 Completed**: Fully integrated Advanced Agent Intelligence, Contextual Understanding & Reliable Multi-Step Execution (`ConversationStateManager`, `ReferenceResolver`, `AmbiguityHandler`, `HierarchicalRouter`, `PlanQualityScorer`, `PromptInjectionDefense`, `TaskResumeManager`, `AdvancedEvaluator`) with 100% test pass rate across 293 tests.

---

## How to Run & Diagnostics

1. **Setup Environment**:
   ```bash
   pip install -e .
   ```

2. **Run Release Check**:
   ```bash
   python -m jarvis --release-check
   ```

3. **Run Diagnostics (`--doctor`)**:
   ```bash
   jarvis --doctor
   ```

4. **Run Self-Test Suite (`--self-test`)**:
   ```bash
   jarvis --self-test
   ```

5. **Launch Application**:
   ```bash
   scripts/start_jarvis.bat
   # or
   python -m jarvis
   ```

6. **Run Test Suite**:
   ```bash
   python -m pytest
   ```

---

## Roadmap Summary

- **Phases 1–22**: ALL COMPLETED (Production Hardened Release v0.1.0)

---

*JARVIS — Built for the Boss.*
