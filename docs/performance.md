# JARVIS CPU-First & Performance Architecture Specification

---

## 1. Core CPU-First Principle

> **"Never require a GPU when a CPU implementation can reasonably accomplish the task."**

JARVIS is built from the ground up to operate on personal computers with **no dedicated GPU, no CUDA, integrated graphics only, and limited RAM (e.g. 8GB or less)**.

GPU acceleration is treated strictly as an optional optimization layer, never a mandatory dependency.

---

## 2. Hardware Profiles & Tier Adaptation

The system automatically inspects physical hardware at bootstrap using `HardwareDetector` (`src/jarvis/system/hardware.py`) and maps resources to one of five operational tiers defined in `config/performance.yaml`:

| Tier | System Criteria | Quantization Standard | Context Limit | Vision Enabled | Worker Limit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ULTRA_LOW`** | $\le 4\text{GB RAM}$ or $\le 2\text{ Cores}$ | `Q3_K_M` (1.5B) | 1,024 Tokens | Disabled | 1 Worker |
| **`LOW`** | $\le 8\text{GB RAM}$ or $4\text{ Cores}$ | `Q4_K_M` (3B) | 2,048 Tokens | Disabled | 2 Workers |
| **`MEDIUM`** | $\le 16\text{GB RAM}$ or $8\text{ Cores}$ | `Q5_K_M` (7B) | 4,096 Tokens | Optional | 4 Workers |
| **`HIGH`** | $\ge 32\text{GB RAM}$ | `Q6_K` (14B) | 8,192 Tokens | Enabled | 8 Workers |
| **`GPU_ACCELERATED`**| Dedicated CUDA VRAM $\ge 6\text{GB}$ | `Q8_0` (14B+) | 16,384 Tokens | Enabled | 8 Workers |

---

## 3. Fast Path Intent Router (`FastIntentRouter`)

To avoid expensive LLM model invocations for deterministic actions, user requests pass through `FastIntentRouter` (`src/jarvis/brain/fast_path.py`):

```text
User Request ("Open Chrome" / "Pause music" / "Take screenshot")
                       │
                       ▼
             [ FastIntentRouter ]
            /                    \
    Matched (Regex)            Unmatched
          │                        │
          ▼                        ▼
[ Direct Tool Execution ]   [ Local LLM Planner ]
  (Latency < 10ms)           (Model Inference)
```

### Deterministic Handlers (Bypassing LLM)
- Application opening & closing (`Chrome`, `Notepad`, `Calculator`, `Terminal`)
- Media controls (`Pause`, `Play`, `Volume Up/Down`, `Mute`)
- System screen capture (`Take screenshot`)

---

## 4. Resource Monitoring & Background Task Throttling

`ResourceManager` (`src/jarvis/system/resource_manager.py`) continuously tracks CPU and RAM load:
- If CPU utilization exceeds **85%** or RAM usage exceeds **90%**, background tasks (file indexing, memory maintenance) are automatically paused until load normalizes.

---

## 5. Task Queue & Concurrency Management

All multi-step actions are scheduled via `TaskQueue` (`src/jarvis/system/task_queue.py`), supporting:
- Priorities (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`)
- Status tracking (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`)
- Controlled thread/worker pool sizing to prevent CPU core thrashing.

---

## 6. Subsystem Performance Optimizations

### 6.1 Vision & Screenshot Optimization
- Screen capture is **never executed continuously at high FPS**.
- Capture occurs only when DOM/accessibility APIs fail or explicit screen analysis is requested.
- Cascading Priority: `Structured API -> DOM/Accessibility -> Application Metadata -> Screenshot -> Vision Model`.

### 6.2 Browser Automation Optimization
- Browser sessions and contexts are persisted and reused across commands instead of launching fresh browser instances per request.

### 6.3 Voice Pipeline Optimization
- STT (Whisper CPU) runs only after a lightweight wake-word detector triggers.
- TTS outputs audio via sentence-level streaming synthesis.

### 6.4 Local Model Performance Modes
Inference resources dynamically adapt based on `performance_modes.active_mode` in `config/models.yaml`:
- **`battery_saver`**: Limits CPU thread usage to 50% of available physical cores, caps context to 1,024 tokens.
- **`balanced`**: Uses 75% of physical cores, caps context to 2,048 tokens.
- **`performance`**: Uses 100% of assigned inference cores, caps context to 4,096 tokens.

### 6.5 Token Streaming Latency
- First token latency is minimized by streaming generated chunks directly to the UI layer as tokens are emitted.
- Mock & native backends implement standard token generator interfaces (`ModelProvider.stream()`).

---

## 7. Performance Latency Targets

| Operation Type | Target Latency (CPU System) |
| :--- | :--- |
| **Fast Path Command Matching** | $< 10\text{ ms}$ |
| **Hardware Auto-Detection** | $< 50\text{ ms}$ |
| **Direct Tool Action Execution** | $< 500\text{ ms}$ |
| **Local LLM Response First Token** | Interactive CPU response |

---

*Performance Architecture Blueprint approved for JARVIS Phase 1.*
