# Universal Computer Agent Guide (Prompt 026)

## Overview
JARVIS has been transformed from a collection of isolated automation tools into a **Universal General-Purpose Computer Agent**. It accepts arbitrary natural-language computer requests, reasons about desired outcomes, discovers available capabilities and UI controls dynamically, plans multi-step execution hierarchies, criticizes and repairs plans before execution, observes computer execution state continuously, verifies outcome evidence, handles interruptions gracefully, and keeps the Boss visually informed throughout task execution.

---

## Key Architecture & Components

```
USER NATURAL-LANGUAGE REQUEST
            │
            ▼
┌──────────────────────────────┐
│       TaskInterpreter        │  <-- Deconstructs intent, domain, recipient, content
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        TaskDecomposer        │  <-- Builds TASK -> SUBTASK -> STEP -> ACTION tree
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          PlanCritic          │  <-- Evaluates plan validity, risk, verification coverage
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  CapabilityDiscoveryEngine   │  <-- Dynamically matches intent to tools/skills
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       ReasoningEngine        │  <-- Executes steps, captures observations, verifies
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    LiveTaskMonitorWidget     │  <-- Real-time UI telemetry for Boss supervision
└──────────────────────────────┘
```

### 1. Natural Language Intent Interpretation (`interpreter.py`)
- Maps requests into `StructuredIntent` objects containing objective (`SEND_EMAIL`, `CROSS_APP_WORKFLOW`, `FILESYSTEM_OPERATION`, `APPLICATION_CONTROL`, `BROWSER_NAVIGATION`), primary domain, target path/URL/recipient, content payloads, completion conditions, and safety approval flags.

### 2. Hierarchical Plan Decomposition (`decomposer.py`)
- Decomposes intents into structured `TaskHierarchy` objects with ordered `TaskNode` execution steps. Each step defines `action_type`, `tool_name`, `parameters`, `preconditions`, `verification_check`, and `risk_level`.

### 3. Plan Critic & Auto-Repairer (`critic.py`)
- Inspects plans prior to execution to verify completeness, prerequisite ordering, risk escalation, and verification coverage. `PlanRepairer` automatically injects missing verification or prerequisite steps.

### 4. Dynamic Capability & UI Discovery (`capability_discovery.py` & `unknown_app_discovery.py`)
- Scans registered tools, skills, and accessibility UI controls in unfamiliar desktop applications without hard-coded app controllers.

### 5. Master Agent Contract (`JarvisAgent`)
- Standard high-level API: `JarvisAgent.execute(user_request) -> TaskExecutionResult`
- Accepts natural language string and returns structured result with goal, steps, actions, observations, verification evidence, confidence score, and response text.

---

## Quick Start & Usage Examples

```python
from jarvis.core.reasoning.reasoning_engine import JarvisAgent

# 1. Execute Filesystem Operation
result = JarvisAgent.execute("Create file at data/test_workspace/hello.txt with content Hello Boss")
print("Status:", result.status)
print("Confidence:", result.confidence)

# 2. Execute Communication Workflow
result = JarvisAgent.execute("Send email to Vasanth saying meeting is postponed to 4 PM")
print("Status:", result.status)  # REQUIRES_CONFIRMATION if policy demands approval

# 3. Execute Cross-Application Workflow
result = JarvisAgent.execute("Read data/test_workspace/report.txt and email summary to Vasanth")
print("Steps Executed:", len(result.steps))
```

---

## Safety & Governance Principles
- **Local-First & CPU-First**: Operates completely on local CPU without cloud AI APIs or external dependencies.
- **Governed Approval Gates**: High-risk actions (e.g. sending email, deleting files) trigger confirmation requirements before final execution.
- **Evidence-Based Verification**: Tasks verify completion via explicit evidence rather than assuming success.
