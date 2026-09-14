# Phase 8: Conversational Chat Engine

## Overview

The MyLLM Conversational Chat Engine provides a clean, modular, CPU-only multi-turn dialogue system built directly on top of the Phase 0–7 MyLLM architecture. It coordinates conversation histories, deterministic serialization templates, context window truncation, KV-cached autoregressive decoding, token-by-token streaming, and JSON session persistence.

```
+-----------------------------------------------------------------------------------+
|                                  ChatEngine                                       |
|                                                                                   |
|  +--------------------+    +--------------------+    +-------------------------+  |
|  |    ChatSession     |    |    ChatHistory     |    |       ChatTemplate      |  |
|  | (JSON persistence, |    | (Ordered messages: |    | (Deterministic format:  |  |
|  |  session metadata) |    |  system, user,     |    |  ### System: ...        |  |
|  +--------------------+    |  assistant)        |    |  ### User: ...          |  |
|                            +--------------------+    |  ### Assistant: ...)    |  |
|                                                      +-------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                          Context Window Manager                             |  |
|  |  - Preserves System Prompt and Latest User Query                            |  |
|  |  - Truncates oldest conversation turns first (turn-level integrity)         |  |
|  |  - Emits ContextInfo telemetry (truncated, removed_messages, tokens)       |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                          Generation & Streaming                             |  |
|  |  - Generator & KVCache integration (Phase 5)                                |  |
|  |  - Invalidation of KV Cache on history modification or truncation           |  |
|  |  - Token-by-token streaming generator (ChatToken: token_id, text, finished) |  |
|  |  - Stop conditions: EOS, max_new_tokens, context_limit                      |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Architecture & Components

### 1. Message Model (`myllm.chat.message`)
- **`ChatMessage`**:
  - `role`: One of `"system"`, `"user"`, or `"assistant"` (case-insensitive, normalized to lowercase).
  - `content`: Text content string.
  - Non-empty policy: `"user"` and `"assistant"` messages must contain non-whitespace text. `"system"` messages can be empty or omitted.
  - Serialization: `to_dict()` and `from_dict()`.
- **`ChatHistory`**:
  - Encapsulates an ordered sequence of `ChatMessage` objects.
  - Methods: `append`, `add_message`, `clear`, `clone`, `to_list`, `from_list`, `last_message`, `len`, `getitem`.

### 2. Conversation Template & Role Safety (`myllm.chat.template`)
Deterministic serialization format aligned with Phase 7:
```
### System:
{system_message}

### User:
{user_message}

### Assistant:
{assistant_message}
```

- **Prompt Construction**: When prompting the model to generate the next assistant turn, the prompt terminates with:
  ```
  ### Assistant:
  ```
- **Optional System Prompt**: If no system prompt is provided, the `### System:` block is omitted entirely (the conversation starts cleanly with `### User:`).
- **Formatting Isolation**: User text containing role header markers like `### System:`, `### User:`, or `### Assistant:` is escaped (`\### ...`) by `sanitize_role_content()`. This ensures user input cannot forge structural role boundaries.

### 3. Context Window Management (`myllm.chat.context`)
Because the model has a finite context length (e.g. 64 or 128 tokens):
- **`ContextManager`**:
  1. Calculates token budget for prompt: `max_allowed_prompt_tokens = context_length - min_response_budget`.
  2. Preserves the overarching system prompt if present.
  3. Preserves the latest user query.
  4. Truncates oldest conversational turns (user/assistant pairs) first to maintain role alternation and conversational coherence.
  5. If even a single turn + system prompt exceeds the budget, it drops the system prompt as a fallback.
- **`ContextInfo`**: Reports `total_tokens`, `used_tokens`, `truncated: bool`, `removed_messages: int`, `system_preserved: bool`.

### 4. KV Cache Lifecycle & Invalidation (`myllm.chat.engine`)
- **Integration**: Reuses the Phase 5 `KVCache` per-layer key/value storage.
- **Invalidation Rules**:
  - Reset: `engine.reset()` clears all KV cache tensors.
  - Turn Boundary: Adding a new user message marks the cache dirty.
  - Context Truncation: Whenever history is truncated, past KV states are discarded and recomputed on the newly truncated prompt to ensure mathematical correctness of causal attention.
  - Independent Sessions: Independent `ChatEngine` instances have isolated caches.

### 5. Streaming & Generation API
- **Streaming**:
  ```python
  for token in engine.stream_response(config):
      if token.finished:
          print(f"\nStopped due to: {token.stop_reason}")
      else:
          print(token.text, end="", flush=True)
  ```
  Each `ChatToken` contains `token_id: int`, `text: str`, `finished: bool`, and `stop_reason: Optional[str]`.
- **Batch Generation**:
  ```python
  response = engine.generate_response(config)
  print(response.content)
  print(response.telemetry.tokens_per_second)
  ```
- **Stop Conditions**: Accurately reported as `"eos"`, `"max_new_tokens"`, or `"context_limit"`.

### 6. Session Persistence & Replay (`myllm.chat.session`)
- **`ChatSession`**:
  - `session_id`: Unique UUID.
  - `system_prompt`: Optional system directive string.
  - `messages`: List of serialized message dictionaries.
  - `generation_config`: Dictionary of decoding parameters.
  - `created_at` / `updated_at`: ISO-8601 UTC timestamps.
  - `model_checkpoint` / `tokenizer_fingerprint`: Provenance metadata.
- **Serialization**: Pure JSON via `save_json(path)` and `load_json(path)`. Zero pickle usage.
- **Deterministic Replay**: Restoring a session into a fresh `ChatEngine` produces identical greedy generation outputs.

---

## Interactive CLI Usage

Launch the interactive console with:
```powershell
python scripts/chat.py --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt --tokenizer checkpoints/smoke/tokenizer.json
```

### CLI Slash Commands
- `/exit` or `/quit`: Terminate the chat session.
- `/reset`: Clear conversation history and reset KV cache.
- `/history`: Display the entire conversation history with roles.
- `/save <path>`: Persist current session to a JSON file.
- `/load <path>`: Restore a previously saved conversation session.
- `/help`: Show command documentation.

---

## Performance Benchmark

Run the CPU chat benchmark with:
```powershell
python scripts/benchmark_chat.py --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt --tokenizer checkpoints/smoke/tokenizer.json
```

Measures:
- Prefill latency (prompt encoding)
- Autoregressive generation latency
- Throughput in tokens/second
- KV cache enabled vs disabled speedup.

---

## Known Limitations & Disclaimers

1. **Synthetic Base Model**: The model demonstrated in Phase 7 was trained on a small synthetic dataset for pipeline validation. Responses reflect this limited corpus and do not constitute broad real-world knowledge.
2. **Formatting Isolation**: Role sanitization prevents structural header collision during string concatenation; it does not replace a trained safety or guardrail model.
3. **CPU Throughput**: Throughput scales with CPU clock speed and thread count.
