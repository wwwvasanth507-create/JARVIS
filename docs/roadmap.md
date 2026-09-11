# JARVIS Master Development Roadmap

This document outlines the authoritative 20-phase incremental development roadmap for **JARVIS**. Each phase builds upon the established modular foundation without introducing premature complexity.

---

### Phase 1: Project Foundation & Master Architecture (COMPLETED)
- Established professional directory structure, metadata, configuration schemas, identity, and security permission architecture.

### Phase 2: Production Local Model Runtime & Real LLM Integration (COMPLETED - Prompt 013 Runtime)
- Developed `src/jarvis/brain/` subsystem (`ModelProvider`, `LlamaCppModelProvider`, `MockModelProvider`, `ModelRegistry`, `ContextManager`, `StructuredToolParser`, `ModelMemoryChecker`, `ModelBenchmarkUtility`, `ModelHealthCheck`).
- Built direct `llama.cpp` GGUF local CPU execution (`n_gpu_layers=0`), RAM safety checks, hardware-aware profiles (`ULTRA_LOW` through `GPU_ACCELERATED`), token streaming, cancellation, context window prioritization, structured tool-call parsing, and graceful missing-model fallback.

### Phase 3: Chat Interface (COMPLETED)
- Interactive Command Line Interface (CLI) and chat UI for direct text interaction with the Boss.

### Phase 4: Speech-to-Text (STT) (COMPLETED)
- Integrated local CPU STT engine with microphone audio capture stream and voice activity detection (VAD).

### Phase 5: Text-to-Speech (TTS) (COMPLETED)
- Integrated fast local neural TTS engine producing clear female voice synthesis.

### Phase 6: Wake-Word Detection (COMPLETED)
- Low-power background wake-word engine (listening for "JARVIS") with seamless transition to STT.

### Phase 7: Application Control (COMPLETED - Prompt 009)
- Developed `application.*` toolset (12 structured tools) to discover, launch, focus, monitor, restart, and gracefully close desktop applications across platforms.

### Phase 8: Computer Control (COMPLETED)
- Developed `computer.*` toolset for input actions (mouse movement, clicking, typing, key combinations, active window focus).

### Phase 9: Browser Automation (COMPLETED)
- Developed `browser.*` toolset utilizing Playwright / Chromium for page navigation, element selection, screenshot capturing, and web search extraction.

### Phase 10: Intent Understanding, Planning & Tool Orchestration (COMPLETED - Prompt 010)
- Developed `src/jarvis/core/orchestration/` subsystem (`JarvisOrchestrator`, `IntentParser`, `GoalResolver`, `Planner`, `PlanValidator`, `PlanExecutor`, `ToolDispatcher`, `ObservationManager`, `VerificationManager`, `ConfirmationManager`, `RecoveryManager`, `CancellationManager`).

### Phase 11: Filesystem Intelligence (COMPLETED - Prompt 007)
- Developed `filesystem.*` toolset (16 structured tools) for semantic searching, file reading, atomic writing, targeted editing, duplicate detection, storage reporting, and organization.

### Phase 12: Controlled Shell & Terminal (COMPLETED - Prompt 008)
- Developed `shell.*` toolset (9 structured tools) for safe terminal command execution, environment variable secret redaction, output capping, background job management, and process control.

### Phase 13: Local Screen Understanding, OCR & Vision Layer (COMPLETED - Prompt 014)
- Developed `src/jarvis/computer/vision/` subpackage (`ScreenVisionManager`, `ScreenCapture`, `ScreenPrivacyPolicy`, `OCRProvider`, `UIElementDetector`, `ScreenComparator`, `VisionProvider`, `SpatialLayoutAnalyzer`, `VisualTargetMatcher`, `ScreenState`, `ImagePreprocessor`, `OCRResultCache`, `VisualStateVerifier`).
- Built multi-mode screen capture (`FULL_SCREEN`, `ACTIVE_WINDOW`, `REGION`), application blacklisting, CPU-compatible local OCR with confidence thresholds (`HIGH`, `MEDIUM`, `LOW`), multi-layered visual element detection, before/after screen change comparison, 6 screen tools (`screen.capture`, `screen.read_text`, `screen.analyze`, `screen.find`, `screen.describe`, `screen.compare`), and 4 builtin skills (`read_screen`, `find_on_screen`, `describe_screen`, `verify_visual_state`).

### Phase 14: Persistent Memory & Knowledge System (COMPLETED - Prompt 011)
- Developed `src/jarvis/memory/` subpackage (`MemoryManager`, `DatabaseManager`, `SchemaMigrator`, `MemoryStorage`, `MemoryPrivacyPolicy`, `MemoryDeduplicator`, `FactManager`, `KnowledgeIndexer`, `MemoryRetriever`).

### Phase 15: Modular Skill System (COMPLETED - Prompt 012)
- Developed `src/jarvis/skills/` subpackage (`SkillManager`, `SkillRegistry`, `SkillLoader`, `SkillDiscovery`, `SkillResolver`, `SkillPlanner`, `SkillExecutor`, `SkillPermissionChecker`, `SkillSafetyPolicy`).

### Phase 16: Document Intelligence & Local Processing (COMPLETED - Prompt 013 Document Processing)
- Developed `src/jarvis/documents/` subpackage (`DocumentManager`, `DocumentDetector`, `DocumentMetadataExtractor`, `DocumentNormalizer`, `DocumentChunker`, `DocumentCache`, `DocumentRegistry`, `DocumentReader`, `TableExtractor`, `DocumentSummarizer`, `DocumentAnalyzer`, `DocumentComparer`, `DocumentCreator`, `DocumentConverter`, `DocumentSecurityPolicy`, `DocumentPrivacyManager`, `DocumentVerificationManager`).

### Phase 17: Closed-Loop Self-Recovery & Replanning (COMPLETED - Prompt 015)
- Developed `src/jarvis/core/recovery/` subpackage (`JarvisRecoveryManager`, `FailureClassifier`, `DiagnosticEngine`, `RecoveryPlanner`, `RecoveryExecutor`, `RecoveryPolicy`, `DiagnosticReplanner`, `EvidenceCollector`, `StrategyRegistry`).
- Built extensible failure classification, confidence-scored root-cause analysis (`RootCause`), deterministic subsystem diagnostics (`DiagnosticEvidence`), pre-registered recovery strategies (`RETRY_ONCE`, `REFRESH_STATE`, `REQUERY_FILESYSTEM`, `RELOAD_BROWSER_PAGE`, `REBUILD_PLAN`, `REQUEST_USER`), mandatory permission re-checking, human intervention protocol (`HumanInterventionRequiredError`), loop protection (`RecoveryLoopDetectedError`), and diagnostic replanning.

### Phase 18: Task Scheduling & Background Automation (COMPLETED - Prompt 016)
- Developed `src/jarvis/scheduler/` subpackage (`SchedulerManager`, `ScheduleParser`, `TaskPersistence`, `TaskScheduler`, `TaskWorkerPool`, `TaskExecutor`, `NotificationManager`, `SchedulerPolicy`, `TaskCanceller`, `SchedulerRecovery`, `BoundedSchedulerQueue`).
- Built natural-language schedule parser, timezone-aware recurrence engine, SQLite persistence (`scheduled_tasks`, `task_runs`), 0.0% idle CPU event loop, mandatory orchestrator dispatch pipeline, runtime permission re-evaluation, multi-channel notification fallback (Text -> Desktop -> Voice), Prompt 015 recovery integration, 8 `scheduler.*` tools, and 6 builtin skills (`schedule_task`, `cancel_task`, `list_tasks`, `pause_task`, `resume_task`, `task_history`).

### Phase 19: Automated Evaluation & Performance Benchmarking (COMPLETED - Evaluation Baseline)
- Automated evaluation suite (`tests/evaluation/`) testing task completion rate, tool call precision, and resource utilization.

### Phase 20: Production Hardening, Real End-to-End Runtime & Distribution (COMPLETED - Prompt 017)
- Consolidated single application entry point (`src/jarvis/app.py`, `python -m jarvis`, `jarvis` CLI).
- Implemented explicit application lifecycle state machine (`ApplicationLifecycle`), hardware-aware performance modes (`ULTRA_LOW` through `GPU_ACCELERATED`), capability registry (`CapabilityRegistry`), CLI diagnostic tool (`jarvis --doctor`), self-test suite (`jarvis --self-test`), performance benchmark suite (`PerformanceBenchmark`), Windows batch and PowerShell launchers (`start_jarvis.bat`, `start_jarvis.ps1`), explicit user-controlled autostart manager (`AutostartManager`), end-to-end integration test suite, false-success defense, and production readiness documentation (`docs/production-readiness.md`).

### Phase 21: Production Desktop UI, System Tray & Unified Runtime (COMPLETED - Prompt 018)
- Developed PySide6/Qt6 modern desktop GUI shell (`src/jarvis/ui/`) with dark theme styling, glassmorphism UI elements, customizable accent colors, system tray integration, reactive task state visualization, audio visualizer, hotkey listeners, and system notification dispatch.

### Phase 22: Advanced Agent Intelligence, Contextual Understanding & Reliable Multi-Step Execution (COMPLETED - Prompt 019)
- Implemented `ConversationStateManager` for bounded active task, entity, and application state tracking.
- Implemented `ReferenceResolver` for contextual pronoun ("it", "that") and ordinal ("the second song", "the 1st result") reference resolution against active state.
- Implemented `AmbiguityHandler` for first-class structured ambiguity representation (`StructuredAmbiguity`, `AmbiguityCandidate`) and targeted clarification flows.
- Implemented `HierarchicalRouter` (`RoutingTier.FAST_PATH` -> `DETERMINISTIC` -> `SKILL_RESOLVER` -> `CONTEXTUAL_RESOLVER` -> `LOCAL_LLM` -> `VISUAL_REASONING`) to ensure zero unnecessary LLM invocations for simple requests.
- Implemented `PlanQualityScorer` for validating multi-step execution plans before execution.
- Implemented `PromptInjectionDefense` for isolating untrusted external web/document payloads and preventing instruction hijacking.
- Implemented `TaskResumeManager` for post-restart interrupted task state persistence and safe resume protocols.
- Implemented `AdvancedEvaluator` with `golden_tasks.json` evaluation dataset and zero-latency benchmark execution (`data/cache/agent-intelligence-benchmark.json`).
- Verified 100% test pass rate across 293 unit and integration tests.

### Phase 23: Real-World Computer Agent Capabilities, Proactive Context & Advanced Workflow Automation (COMPLETED - Prompt 020)
- Implemented `CapabilityInventory` (`src/jarvis/core/capabilities/capability_inventory.py`) tracking machine-readable runtime capability metadata across 12 categories (`APPLICATION`, `COMPUTER`, `BROWSER`, `FILESYSTEM`, `DOCUMENT`, `SHELL`, `VOICE`, `VISION`, `MEMORY`, `SCHEDULER`, `NOTIFICATION`, `SYSTEM`).
- Developed `WorkflowEngine` (`src/jarvis/core/workflows/engine.py`) and parameterized `WorkflowTemplateRegistry` (`templates.py`) supporting 11 workflow states (`DRAFT` through `COMPLETED`).
- Built controlled system clipboard controller (`src/jarvis/computer/clipboard.py`) and 4 clipboard tools (`computer.read_clipboard`, `computer.write_clipboard`, `computer.clear_clipboard`, `computer.inspect_clipboard`) with credential redaction and zero continuous background logging.
- Developed internal event `NotificationCenter` (`src/jarvis/system/notification_center.py`) managing alerts across 7 categories.
- Built conservative `ProactiveContextEngine` (`src/jarvis/core/orchestration/proactive_context.py`) and governed background `MonitorManager` (`src/jarvis/system/monitors.py`) for user-defined condition watching with resource budgets.
- Developed desktop `PrivacyDashboardManager` (`src/jarvis/system/privacy_dashboard.py`), user-facing `ActionJournal` (`src/jarvis/observability/action_journal.py`) with secret masking, and 5 system tools (`system.get_info`, `system.check_cleanup`, `system.network_status`, `system.batch_preview`, `system.replay_task`).
- Created 50-scenario real-world evaluation dataset (`tests/evaluation/real_world_dataset.json`) and verified 100% test pass rate across 316 unit and integration tests.

### Phase 24: Advanced Perception, Application Semantics, Long-Running Supervision & Reliable Agent Memory (COMPLETED - Prompt 021)
- Implemented `LongRunningTaskManager` (`src/jarvis/core/tasks/task_manager.py`) and `TaskHeartbeat` supporting 13 governed task statuses (`CREATED` through `EXPIRED`).
- Developed `TaskSupervisorEngine` (`src/jarvis/core/tasks/supervisor.py`) and `StallDetector` (`src/jarvis/core/tasks/stall_detector.py`) with post-restart orphan task reconciliation.
- Built lightweight `EnvironmentFingerprint` and Checkpoints 2.0 with pre-resume environment, state, and permission re-validation.
- Developed `ApplicationSemanticState` and `BaseApplicationSemanticAdapter` (`src/jarvis/applications/application_semantics.py`) across 6 app families (Browser, File Explorer, Text Editor, Terminal, Document Viewer, Office).
- Developed `UIStateModel` and `UIStateDiffEngine` (`src/jarvis/computer/vision/ui_state_model.py`) with confidence-aware perception (`HIGH`, `MEDIUM`, `LOW`) and multi-tier target resolution (`SemanticTargetResolver`).
- Built bounded `ObservationCache` (`src/jarvis/core/orchestration/observation_cache.py`) with TTL freshness and mandatory pre-action re-observation (`ActiveReobserver`).
- Developed local typed `JarvisEventBus` (`src/jarvis/system/event_bus.py`) with event deduplication/coalescing across 15 event types and task event streaming.
- Developed `StrategyMemory` and failure pattern learning (`src/jarvis/memory/strategy_memory.py`) for long-term task strategy tracking without blind replay.
- Developed central `ResourceArbitrator` (`src/jarvis/system/resource_arbitrator.py`) for bounded resource allocation across Model, Browser, Vision, Voice, and Microphone leases.
- Developed `UserTakeoverDetector` (`src/jarvis/system/user_takeover.py`) for background task state change detection and clean "Safe Handoff" user interaction handling.
- Extended PySide6 desktop app (`src/jarvis/ui/`) with user-facing Task Supervision Panel, Live Event Stream, and Task Detail Views.
- Created 100-scenario evaluation dataset (`tests/evaluation/evaluation_100_scenarios.json`), chaos test suite, security adversarial test suite, and performance benchmarks.
- Verified 100% test pass rate across 341 unit and integration tests.

### Phase 25: Advanced Multimodal Perception, Semantic Computer Interaction & Reliable UI Automation (COMPLETED - Prompt 022)
- Unified Semantic Computer Interaction Layer (`SemanticComputerInteractor`) with `find_element`, `click_element`, `double_click_element`, `right_click_element`, `type_into_element`, `select_element`, `scroll_to_element`, `focus_element`, `read_element`, `inspect_element`, `wait_for_element`, `drag_element`, `fill_form`, and `select_table_row`.
- Common `UIElement` representation and `PerceptionSource` hierarchy (`ACCESSIBILITY/DOM (0.98/0.95)` > `APPLICATION_API (0.90)` > `OCR (0.75)` > `VISUAL (0.60)` > `VLM (0.45)`).
- Structured target queries (`TargetQuery`) and geometric spatial relations (`above`, `below`, `left_of`, `right_of`, `near`, `inside`, `contains`, `next_to`, `before`, `after`, `same_row`, `same_column`).
- Structured ambiguity handling (`AmbiguousTargetError` / multi-candidate breakdown).
- High-level semantic models for Tables (`Table`, `TableRow`, `TableCell`), Forms (`Form`, `FormField`, `FormPreview`), and Dialogs (`UIDialog`, `DialogManager` with security prompt protection).
- Intelligent Wait-For-Condition Engine (`SemanticWaitEngine`) with bounded polling replacing arbitrary fixed sleeps.
- Governed `TargetLease` with TTL expiration and state hash validation before side-effect actions.
- Windows UI Automation native adapter (`WindowsUIAutomationAdapter`), Playwright DOM semantic adapter (`BrowserSemanticAdapter`) with stale handle defense, and local CPU OCR (`OCRProvider`) with English and Tamil support.
- Local VLM 2.0 (`VLMPerceptionAdapter`) with Region-Of-Interest (ROI) cropping and strict untrusted perception data pipeline.
- End-to-End Local Document -> Form binding workflow (`DocumentFormWorkflow`) with pre-submission preview and permission confirmation gates.
- Reusable semantic user macros (`SemanticMacro`, `MacroRegistry`) with versioning and safety validation.
- 5 new semantic tools (`computer.find_element`, `computer.click_element`, `computer.type_element`, `computer.wait_element`, `computer.fill_form`) registered in tool registry.
- Local UI HTTP fixture server (`LocalUIFixtureServer`) and 14 End-to-End Acceptance Scenarios (A through N).
- Expanded 150-scenario evaluation dataset (`tests/evaluation/evaluation_150_scenarios.json`) and latency performance benchmark (`tests/evaluation/performance/ui_perception_benchmark.py`).
- Verified 100% test pass rate across 363 unit and integration tests.

---

*Master Roadmap approved for JARVIS.*
