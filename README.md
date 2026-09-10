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

---

## How to Initialize & Run

1. **Requirements**: Python 3.10+ (Tested on Python 3.14.7 on Windows 11).
2. **Setup virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install project in editable mode**:
   ```bash
   pip install -e .
   ```
4. **Run Unit Tests**:
   ```bash
   pytest
   ```

---

## Roadmap Summary

1. **Phase 1**: Project Foundation & Architecture (Current)
2. **Phase 2**: Local Model Integration (`llama.cpp` GGUF engine)
3. **Phase 3**: Chat Interface
4. **Phase 4–6**: Voice Pipeline (STT, TTS, Wake-Word)
5. **Phase 7–13**: OS, Browser, Vision & File Automation
6. **Phase 14–20**: Memory, Skills, Self-Recovery & Hardening

---

*JARVIS — Built for the Boss.*
