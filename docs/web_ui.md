# MyLLM Web UI Documentation (Phase 10)

## Overview

Phase 10 introduces a responsive, browser-based chat interface for **MyLLM**. The Web UI communicates strictly with the local FastAPI REST and Server-Sent Events (SSE) streaming API established in Phase 9.

All model inference remains **100% server-side on CPU**. The browser client contains **zero** PyTorch dependencies, **zero** model weights, and **zero** inference or tokenization logic.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (Client)                     │
│  React 19 + TypeScript + Vite                               │
│  - Session state & optimistic message list                  │
│  - SSE stream consumption & token buffer accumulation       │
│  - Safe Markdown / Code block rendering (XSS sanitized)     │
│  - Parameter configuration (temp, top-p, max tokens)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / SSE
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 MyLLM Local API Server (FastAPI)            │
│  http://127.0.0.1:8000                                      │
│  - CORS Middleware: whitelisted localhost:5173              │
│  - In-memory session manager with context window management │
│  - SSE Streaming endpoint (/v1/sessions/{id}/messages/stream)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     ChatEngine (Phase 8)                    │
│  - Multi-turn conversation management                       │
│  - Context truncation to 64 tokens                          │
│  - Streaming generator with KV cache lifecycle              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            GPTModel (Phase 2) + Tokenizer (Phase 1)         │
│  - 84,384 parameter GPT-style decoder-only Transformer      │
│  - Phase 7 Supervised Fine-Tuning (SFT) checkpoint          │
│  - Byte-Level BPE Tokenizer (305 vocabulary)                │
│  - Strict CPU computation                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

- **Framework**: React 19 (`react`, `react-dom`)
- **Language**: TypeScript (`tsc -b`, `verbatimModuleSyntax`, `erasableSyntaxOnly`)
- **Bundler / Dev Server**: Vite 8
- **Styling**: Vanilla CSS Design System with dark mode, glassmorphism, responsive breakpoints, and modern typography (Google Fonts: *Inter*, *JetBrains Mono*, *Outfit*)
- **Testing**: Vitest + `@testing-library/react` + `happy-dom`
- **Linting**: Oxlint

---

## 3. Directory Structure

```
frontend/
├── dist/                      # Production build bundle
├── src/
│   ├── components/
│   │   ├── ChatWindow.tsx     # Message list, empty state, starter prompts
│   │   ├── CodeBlock.tsx      # Syntax-styled code block with copy action
│   │   ├── Composer.tsx       # Auto-resizing textarea with Enter to send
│   │   ├── Header.tsx         # Brand logo, CPU connection badge, modals
│   │   ├── MessageBubble.tsx  # Message bubble with markdown & telemetry
│   │   ├── ModelModal.tsx     # Model introspection modal
│   │   ├── SettingsModal.tsx  # Generation parameters and system prompt modal
│   │   └── Sidebar.tsx        # Session drawer, New Chat, session persistence
│   ├── hooks/
│   │   ├── useChat.ts         # Central chat state, SSE streaming, sessions
│   │   ├── useHealth.ts       # Periodic API health polling with retry
│   │   └── useModelInfo.ts    # Model metadata introspection hook
│   ├── services/
│   │   └── apiClient.ts       # Typed HTTP and SSE streaming client
│   ├── tests/
│   │   ├── apiClient.test.ts  # API client unit tests
│   │   ├── components.test.tsx# UI component interaction tests
│   │   ├── liveE2E.test.ts    # Live server integration test
│   │   ├── markdown.test.ts   # HTML sanitization and markdown tests
│   │   └── useChat.test.ts    # Conversational state management tests
│   ├── types/
│   │   └── api.ts             # TypeScript interfaces matching FastAPI schemas
│   ├── utils/
│   │   └── markdown.ts        # Zero-dependency safe Markdown parser
│   ├── App.tsx                # Top-level application layout coordinator
│   ├── index.css              # Modern dark-mode design system
│   └── main.tsx               # Application entrypoint
├── index.html                 # HTML shell with meta tags & font imports
├── package.json               # Scripts and dependencies
├── tsconfig.json              # TypeScript solution configuration
└── vite.config.ts             # Vite bundler and vitest configuration
```

---

## 4. Getting Started

### Prerequisites
- Python 3.14+ with PyTorch CPU installed
- Node.js 20+ and npm 10+

### Starting the Backend API Server
```powershell
# From project root (C:\ll\JARVIS)
python scripts/serve.py --host 127.0.0.1 --port 8000
```

### Starting the Frontend Development Server
```powershell
# From frontend directory (C:\ll\JARVIS\frontend)
npm run dev -- --host 127.0.0.1 --port 5173
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

### Configuring the API URL
The API URL defaults to `http://127.0.0.1:8000`. To customize the target API address, set the `VITE_API_URL` environment variable:
```powershell
$env:VITE_API_URL="http://localhost:8000"
npm run dev
```

---

## 5. Production Build & Static Serving

### Building for Production
```powershell
cd frontend
npm run build
```
Output is generated into `frontend/dist/`:
- `dist/index.html` (~0.9 kB)
- `dist/assets/index-*.css` (~15.9 kB)
- `dist/assets/index-*.js` (~244 kB)

### Previewing the Production Build
```powershell
npm run preview
```

---

## 6. Features & Interactions

### Streaming Assistant Responses
When a message is submitted, the UI requests `POST /v1/sessions/{id}/messages/stream`. Tokens are read via a `ReadableStream` reader, accumulated in state, and rendered incrementally with a pulsating cursor indicator. Generation latency, token count, and tokens-per-second (tok/s) are recorded upon completion.

### Abort / Generation Cancellation
A **Stop** button appears during streaming. Triggering Stop invokes `AbortController.abort()`, terminating the HTTP connection, preserving partial streamed text, and releasing the input composer.

### Safe Markdown & Code Rendering
- Raw HTML strings are strictly escaped (`&`, `<`, `>`, `"`, `'`) before parsing.
- Fenced code blocks (` ```python `) are parsed into distinct code elements with a one-click **Copy to Clipboard** action.
- Inline code (` `code` `), bold (`**text**`), italic (`*text*`), and bullet lists are rendered safely.

### Session Management
- **New Chat**: Starts a fresh conversational context on the server.
- **Switching**: Clicking any past conversation loads its server-side history.
- **Delete**: Removes the session from the backend in-memory registry.
- **Save to Disk**: Calls `POST /v1/sessions/{id}/save` to persist the conversation JSON file to the server filesystem.

### Generation Settings & System Prompt
The Settings modal provides interactive controls:
- **System Directive**: Conditioning prompt sent when initializing new chat sessions.
- **Decoding Mode**: Toggle between Greedy (deterministic) and Sampling.
- **Sliders**: `max_new_tokens` (4–64), `temperature` (0.1–2.0), `top_p` (0.1–1.0), and optional random `seed`.

---

## 7. Security Considerations

1. **Local-Only Operation**: Designed for local development on `127.0.0.1`. No external network calls are performed.
2. **Untrusted LLM Output**: All generated text is treated as untrusted and passed through entity sanitization before DOM injection. Script tags or malicious attributes cannot execute.
3. **No Automatic Code Execution**: Code blocks provide a copy action only; code is never executed automatically.
4. **CORS Whitelist**: The API server explicitly restricts CORS access to `localhost:5173`, `127.0.0.1:5173`, `localhost:3000`, and `127.0.0.1:3000`. No wildcard `*` is used.

---

## 8. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Disconnected badge in header** | API server is not running on port 8000 | Run `python scripts/serve.py --host 127.0.0.1 --port 8000` |
| **CORS Network Error in console** | API server running with outdated code without CORS | Restart the server using the latest `scripts/serve.py` |
| **Context Overflow Error** | Total dialogue tokens exceeded the 64-token context length | Click **New Chat** to reset dialogue context |
