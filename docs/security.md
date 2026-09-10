# Master Security & Privacy Policy for JARVIS

## Core Guarantees
1. **Local Sovereignty**: All reasoning, planning, memory storage, OCR, TTS, STT, and scheduling execute locally on user hardware. Zero cloud AI API keys (OpenAI, Anthropic, Gemini API) or Ollama dependencies.
2. **Permission Hierarchy**: Every tool invocation passes `PermissionEvaluator` checks against `config/permissions.yaml` categories (`READ_FILES`, `WRITE_FILES`, `DELETE_FILES`, `RUN_COMMANDS`, `COMPUTER_CONTROL`, `BROWSER_CONTROL`, `APPLICATION_CONTROL`, `SYSTEM_CONTROL`) and risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
3. **Prompt Injection Defense**: External web text and documents are scanned by `PromptInjectionDefense` and wrapped in `[UNTRUSTED CONTENT PAYLOAD (...)]` blocks.
4. **Clipboard Protection**: Clipboard content is inspected for credential patterns and redacted before return. Zero background continuous logging.
5. **Bulk Side-Effect Guards**: Batch operations (>5 files) trigger safety previews and user confirmations.
