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

### Phase 7: Application Control (COMPLETED - Prompt 009)
- Developed `application.*` toolset (12 structured tools) to discover, launch, focus, monitor, restart, and gracefully close desktop applications across Windows, Linux, and macOS.
- Built application registry (`config/applications.yaml`), index cache (`data/indexes/applications.json`), alias & ambiguity resolution, unsaved-work guarding, readiness polling, and health checking.


### Phase 8: Keyboard and Mouse Control
- Develop `computer.*` toolset for simulated input actions (mouse movement, clicking, dragging, typing, key combinations).
- Implement safety boundaries, fail-safe corners, and coordinate scaling.

### Phase 9: Browser Automation
- Develop `browser.*` toolset utilizing Playwright / Chromium in local headful/headless mode.
- Support page navigation, form filling, element selection, screenshot capturing, and web search extraction.

### Phase 10: Intent Understanding, Planning & Tool Orchestration (COMPLETED - Prompt 010)
- Developed `src/jarvis/core/orchestration/` subsystem (`JarvisOrchestrator`, `IntentParser`, `GoalResolver`, `Planner`, `PlanValidator`, `PlanExecutor`, `ToolDispatcher`, `ObservationManager`, `VerificationManager`, `ConfirmationManager`, `RecoveryManager`, `CancellationManager`).
- Built deterministic fast-path routing, multi-step plan generation with static policy validation, tokenized confirmation handling, post-condition verification, single-retry step recovery, loop detection, and real-time cancellation.

### Phase 11: Filesystem Intelligence (COMPLETED - Prompt 007)
- Developed `filesystem.*` toolset (16 structured tools) for semantic searching, file reading, atomic writing, targeted editing, duplicate detection, storage reporting, organization planning, and directory tree navigation.
- Enforced strict permission boundaries (`READ_FILES`, `WRITE_FILES`, `DELETE_FILES`), path safety confinement, and empirical verification.

### Phase 12: Terminal / Tool Execution (COMPLETED - Prompt 008)
- Developed `shell.*` toolset (9 structured tools) for safe terminal command execution, environment variable secret redaction, output capping, background job management, and process control.
- Enforced strict allowlist/denylist validation, dangerous pattern blocking, zero autonomous privilege escalation, working directory confinement, and audit logging.


### Phase 13: Screen Understanding & Computer Vision
- Integrate local vision models (e.g., Moondream / LLaVA / Florence-2 CPU) for screen analysis.
- Enable visual element detection, OCR extraction, and UI layout interpretation.

### Phase 14: Memory & Knowledge System (COMPLETED - Prompt 011)
- Developed `src/jarvis/memory/` subpackage (`MemoryManager`, `DatabaseManager`, `SchemaMigrator`, `MemoryStorage`, `MemoryPrivacyPolicy`, `MemoryDeduplicator`, `PreferenceManager`, `FactManager`, `EpisodeManager`, `ProjectManager`, `TaskManager`, `MemoryExtractor`, `RetentionManager`, `KnowledgeIndexer`, `MemoryRetriever`, `KnowledgeRetriever`).
- Built local SQLite database (`data/database/memory.db`), explicit memory categories, pattern-matched privacy policy blocking credential storage, conflict deduplication, incremental Markdown knowledge indexing (SHA256), multi-signal ranking, and context builder.

### Phase 15: Skill System (COMPLETED - Prompt 012)
- Developed `src/jarvis/skills/` subpackage (`SkillManager`, `SkillRegistry`, `SkillLoader`, `SkillDiscovery`, `SkillResolver`, `SkillPlanner`, `SkillExecutor`, `SkillValidator`, `SkillPermissionChecker`, `SkillSafetyPolicy`, `SkillLifecycleManager`, `SkillDependencyManager`, `SkillVersionManager`).
- Built declarative YAML manifest format (`skills/`), skill discovery, validation, intent resolution, permission intersection, effective risk escalation, 5 builtin skills (`open_application`, `find_file`, `open_file`, `web_search`, `system_status`), and 6 skill management tools (`skill.list`, `skill.find`, `skill.info`, `skill.enable`, `skill.disable`, `skill.status`).

### Phase 16: Document Intelligence & Local Document Processing (COMPLETED - Prompt 013)
- Developed `src/jarvis/documents/` subpackage (`DocumentManager`, `DocumentDetector`, `DocumentMetadataExtractor`, `DocumentNormalizer`, `DocumentChunker`, `DocumentCache`, `DocumentRegistry`, `DocumentReader`, `TableExtractor`, `DocumentSummarizer`, `DocumentAnalyzer`, `DocumentComparer`, `DocumentCreator`, `DocumentConverter`, `DocumentSecurityPolicy`, `DocumentPrivacyManager`, `DocumentVerificationManager`).
- Built format-specific extractors (`.txt`, `.md`, `.json`, `.yaml`, `.csv`, `.html`, `.xml`, `.pdf`, `.docx`), structural chunking, table extraction, document summarization, QA with grounded citations, document comparison diffs, atomic document creation, format conversion, prompt injection defense, 7 builtin skills, and 10 document tools (`document.*`).


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
