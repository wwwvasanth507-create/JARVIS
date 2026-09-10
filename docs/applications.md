# JARVIS Application Control & System Integration Architecture

The Application Control Subsystem enables JARVIS to discover, launch, monitor, focus, and gracefully close installed desktop applications across Windows, Linux, and macOS.

## Architecture Overview

```
LLM / Natural Language Request
         │
         ▼
Tool Subsystem (`application.*` tools)
         │
         ▼
`ApplicationManager` (Central Orchestrator)
    ├── `ApplicationRegistry` (`config/applications.yaml` & Cache Index)
    ├── `ApplicationDiscovery` (`data/indexes/applications.json` Cache)
    ├── `AliasResolver` (Exact, Alias & Partial Query Matching + Ambiguity Guard)
    ├── `ApplicationPermissionChecker` (Policy & Risk Tier Evaluation)
    ├── `ApplicationSafety` (Security App Protection & Unsaved Work Detector)
    ├── `ApplicationLauncher` (Structured Launch & File/URL Association)
    ├── `ApplicationController` (Graceful Close, Focus, Restart & Health)
    ├── `ApplicationProcess` (Safe `psutil` Process & Window Metrics)
    └── `ApplicationVerifier` (Post-Execution Empirical Verification)
```

## Key Capabilities

1. **OS-Native Application Discovery**: Discovers installed software natively (Windows Start Menu / App Paths, Linux `.desktop` entries, macOS `.app` bundles) and caches metadata in `data/indexes/applications.json`.
2. **Natural Alias & Ambiguity Resolution**: Resolves natural aliases ("code" → VS Code, "browser" → Chrome). If a query matches multiple distinct applications (e.g. "Open browser" matching Chrome and Firefox), raises `AmbiguousApplication` and requests Boss clarification.
3. **Unsaved Work Guarding**: Detects text editors and IDEs holding unsaved changes; requests graceful closure and requires explicit confirmation before force closing.
4. **Window Focus Integration**: Integrates directly with Prompt 005's `WindowManager` (`computer.focus_window`).
5. **File & URL Association**: Safely opens document paths and web URLs through Prompt 007's filesystem safety and system browser abstractions.
