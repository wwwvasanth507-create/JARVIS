# Phase 9: Local API Server Documentation

## Overview

The MyLLM Local API Server provides an asynchronous ASGI HTTP interface built on FastAPI and Uvicorn. It wraps the Phase 8 `ChatEngine` to expose stateful multi-turn conversation sessions, synchronous response generation, real-time Server-Sent Events (SSE) streaming, model metadata introspection, and explicit JSON session persistence.

```
Client (HTTP / SSE)
        │
        ▼
FastAPI ASGI Server (src/myllm/api/app.py)
        │
        ▼
APIService & SessionRegistry (src/myllm/api/service.py, sessions.py)
        │
        ▼
ChatEngine (src/myllm/chat/engine.py)
        │
        ▼
KVCache & Generator (src/myllm/inference/)
        │
        ▼
GPTModel & Tokenizer (CPU-only, in eval() mode)
```

---

## Architectural Separation

The API layer acts strictly as a communication and state-coordination adapter:
- **Zero Generation Logic**: The API layer contains no forward-pass loops, token samplers, or attention caching code. It delegates all generation to `ChatEngine.generate_response()` and `ChatEngine.stream_response()`.
- **Model Weight Sharing**: The underlying `GPTModel` and `Tokenizer` are loaded once in read-only evaluation mode (`eval()`, `torch.no_grad()`).
- **Session State Isolation**: Each active session receives its own `ChatEngine` instance with independent `ChatHistory` and independent `KVCache`. State is never shared across sessions.

---

## Concurrency Model

Because the model forward pass and KV cache operations execute on CPU:
1. **Per-Session Lock**: Each active session contains an `asyncio.Lock`. Concurrent requests targeting the *same* session are serialized to prevent corrupting that session's conversational turn order or KV cache tensors.
2. **Global Inference Lock**: An `asyncio.Lock` wraps forward-pass execution across threads to ensure stable CPU cache utilization and prevent core thrashing during concurrent requests from different sessions.

---

## Configuration

Server configuration is governed by `ServerConfig`:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `host` | `str` | `"127.0.0.1"` | Bind host interface (localhost only by default) |
| `port` | `int` | `8000` | Port to listen on |
| `device` | `str` | `"cpu"` | Compute device (strictly enforced as `"cpu"`) |
| `checkpoint` | `str` | `"experiments/phase7/.../best.pt"` | Path to model weights checkpoint |
| `tokenizer` | `str` | `"data/tokenized/tokenizer.json"` | Path to tokenizer JSON |
| `max_sessions` | `int` | `100` | Maximum simultaneous active sessions |
| `max_message_length` | `int` | `4096` | Maximum user message character length |
| `max_new_tokens` | `int` | `128` | Default ceiling on generated tokens |

---

## Server Startup & CLI

Start the server using:
```powershell
python scripts/serve.py `
  --host 127.0.0.1 `
  --port 8000 `
  --checkpoint experiments/phase7/phase7_sft_run/checkpoints/best.pt `
  --tokenizer data/tokenized/tokenizer.json
```

Interactive OpenAPI documentation is automatically available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

---

## Endpoints Reference

### 1. Health Check
- **`GET /health`**
- **Description**: Returns server status and compute device without executing model inference.
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "service": "MyLLM",
    "device": "cpu"
  }
  ```

### 2. Model Information
- **`GET /v1/model`**
- **Description**: Returns model dimensions, parameter counts, context length, and tokenizer fingerprint.
- **Response `200 OK`**:
  ```json
  {
    "model_name": "MyLLM-GPT",
    "checkpoint": "experiments/phase7/phase7_sft_run/checkpoints/best.pt",
    "parameter_count": 84384,
    "context_length": 64,
    "vocab_size": 305,
    "tokenizer_fingerprint": "a89c78921e8b...",
    "device": "cpu",
    "kv_cache_supported": true
  }
  ```

### 3. Create Session
- **`POST /v1/sessions`**
- **Request Body**:
  ```json
  {
    "system_prompt": "You are a concise AI assistant.",
    "generation_config": {
      "max_new_tokens": 32,
      "temperature": 0.7,
      "top_p": 0.9,
      "do_sample": false
    }
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "created_at": "2026-09-14T10:45:00.000Z",
    "model": "MyLLM-GPT",
    "context_length": 64,
    "system_prompt": "You are a concise AI assistant."
  }
  ```

### 4. Get Session Details
- **`GET /v1/sessions/{session_id}`**
- **Response `200 OK`**:
  ```json
  {
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "system_prompt": "You are a concise AI assistant.",
    "messages": [
      {"role": "user", "content": "What is 2 + 2?"},
      {"role": "assistant", "content": "4"}
    ],
    "generation_config": {"max_new_tokens": 32, "do_sample": false},
    "created_at": "2026-09-14T10:45:00.000Z",
    "updated_at": "2026-09-14T10:45:05.000Z",
    "model_checkpoint": "experiments/phase7/.../best.pt"
  }
  ```

### 5. Delete Session
- **`DELETE /v1/sessions/{session_id}`**
- **Description**: Releases session memory, flushes its KV cache, and deletes it from the registry.
- **Response `200 OK`**:
  ```json
  {
    "status": "deleted",
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
  ```

### 6. Send Message (Synchronous)
- **`POST /v1/sessions/{session_id}/messages`**
- **Request Body**:
  ```json
  {
    "content": "Explain gravity in one short sentence.",
    "generation_config": {
      "max_new_tokens": 20
    }
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "message": {
      "role": "assistant",
      "content": "Gravity is the fundamental force pulling objects together."
    },
    "telemetry": {
      "prompt_tokens": 18,
      "generated_tokens": 10,
      "total_tokens": 28,
      "tokens_per_second": 485.2,
      "generation_latency": 0.0206,
      "stop_reason": "eos",
      "context_truncated": false,
      "removed_messages": 0
    }
  }
  ```

### 7. Send Message (Streaming Server-Sent Events)
- **`POST /v1/sessions/{session_id}/messages/stream`**
- **Header**: `Accept: text/event-stream`
- **Request Body**:
  ```json
  {
    "content": "Count from 1 to 3."
  }
  ```
- **Stream Output**:
  ```
  data: {"token": "1", "finished": false}

  data: {"token": ", 2", "finished": false}

  data: {"token": ", 3", "finished": false}

  data: {"token": "", "finished": true, "stop_reason": "eos"}
  ```

### 8. Explicit Session Persistence
- **`POST /v1/sessions/{session_id}/save`**
- **Request Body**:
  ```json
  {
    "path": "scratch/saved_session.json"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "status": "saved",
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "path": "scratch/saved_session.json"
  }
  ```

---

## Error Handling

All client and server errors return structured JSON:
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session '...' not found."
  }
}
```

Standard error codes:
- `SESSION_NOT_FOUND` (`404`): Session ID is not in the registry.
- `VALIDATION_ERROR` (`400`): Request payload failed schema validation (e.g. empty content).
- `INVALID_REQUEST` (`400`): Message length exceeded or invalid parameter combination.
- `MAX_SESSIONS_EXCEEDED` (`429`): Active session count reached capacity limit.
- `INTERNAL_SERVER_ERROR` (`500`): Unexpected server error (stack traces hidden from response).

---

## Local Security Model & Disclaimers

1. **Localhost Binding**: By default, the service binds to `127.0.0.1` and is designed exclusively for local development and paired frontends.
2. **No Authentication / Authorization**: There is no user authentication, token auth, or role-based access control.
3. **No TLS / HTTPS**: The local server runs plain HTTP. It is not designed to be exposed directly to the public internet.
4. **Explicit Persistence Only**: Conversations remain in volatile CPU memory by default; sessions are only persisted to disk when the explicit `/save` endpoint is invoked.
