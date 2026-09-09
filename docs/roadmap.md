# JARVIS Master Development Roadmap

This document outlines the 20-phase incremental development roadmap for **JARVIS**. Each phase builds upon the established modular foundation without introducing premature complexity.

---

### Phase 1: Project Foundation & Master Architecture (CURRENT)
- Establish professional directory structure, metadata, configuration schemas, identity, and security permission architecture.
- Document environment capabilities, master architecture, agent loop, tool abstractions, and knowledge scaling strategy.

### Phase 2: Local Model Integration
- Implement concrete `LocalModelProvider` instances targeting CPU-efficient GGUF engines (via `llama-cpp-python` / C++ native runner).
- Implement prompt template rendering and context window management.

### Phase 3: Chat Interface
- Develop interactive Command Line Interface (CLI) and lightweight desktop chat UI for direct text interaction with the Boss.
- Support streaming response rendering and command history.

### Phase 4: Speech-to-Text (STT)
- Integrate local CPU-optimized STT engine (e.g. Faster-Whisper / Whisper.cpp).
- Add microphone audio capture stream and voice activity detection (VAD).

### Phase 5: Text-to-Speech (TTS)
- Integrate fast local neural TTS engine (e.g. Piper TTS) producing clear female voice synthesis.
- Add audio playback manager with queueing and interruption controls.

### Phase 6: Wake-Word Detection
- Add low-power background wake-word engine (listening for "JARVIS").
- Implement seamless transition from wake-word detection to STT listening mode.

### Phase 7: Application Control
- Develop `application.*` toolset to launch, focus, list, inspect, and gracefully close Windows desktop applications.
- Build application mapping registry (`config/applications.yaml`).

### Phase 8: Keyboard and Mouse Control
- Develop `computer.*` toolset for simulated input actions (mouse movement, clicking, dragging, typing, key combinations).
- Implement safety boundaries, fail-safe corners, and coordinate scaling.

### Phase 9: Browser Automation
- Develop `browser.*` toolset utilizing Playwright / Chromium in local headful/headless mode.
- Support page navigation, form filling, element selection, screenshot capturing, and web search extraction.

### Phase 10: Autonomous Planning
- Implement multi-step goal decomposition engine in `src/jarvis/brain/loop.py`.
- Support plan creation, dynamic task DAG resolution, and step execution monitoring.

### Phase 11: Filesystem Intelligence
- Develop `filesystem.*` toolset for semantic searching, file reading, file writing, directory tree navigation, and diff inspecting.
- Enforce strict permission boundaries (`READ_FILES`, `WRITE_FILES`, `DELETE_FILES`).

### Phase 12: Terminal / Tool Execution
- Develop `shell.*` toolset for executing controlled terminal commands (PowerShell / Command Prompt).
- Add command whitelist/blacklist validation, timeout safety, output capturing, and risk tiering.

### Phase 13: Screen Understanding & Computer Vision
- Integrate local vision models (e.g., Moondream / LLaVA / Florence-2 CPU) for screen analysis.
- Enable visual element detection, OCR extraction, and UI layout interpretation.

### Phase 14: Memory System
- Implement short-term context buffer and long-term persistent memory (`data/database/`).
- Enable episodic interaction recall, preference storage, and semantic vector indexing.

### Phase 15: Skill System
- Build dynamic modular skill loader (`src/jarvis/skills/`).
- Enable loading external domain-specific workflows and procedure recipes without core code modifications.

### Phase 16: Self-Recovery & Replanning
- Implement closed-loop error diagnostic engine.
- When an action verification fails, capture diagnostics, analyze root cause, update planner context, and generate recovery steps.

### Phase 17: Task Scheduling & Background Jobs
- Implement local cron/timer background scheduler for deferred or recurring tasks requested by the Boss.

### Phase 18: Large Knowledge & Prompt Library
- Scale prompt and knowledge repository using frontmatter metadata schemas, hybrid BM25 + vector search, and dynamic context injection.

### Phase 19: Evaluation & Benchmarking
- Implement automated evaluation suite (`tests/evaluation/`) testing agent task completion rate, tool call precision, and resource utilization.

### Phase 20: Production Hardening
- Audit security permissions, optimize binary package footprint, finalize logging/monitoring dashboards, and package offline standalone installer.

---

*Master Roadmap approved for JARVIS.*
