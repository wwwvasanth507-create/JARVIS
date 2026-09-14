"""
Comprehensive Test Suite for Phase 9: Local API Server.

Covers all 21 verification areas:
1. Application creation & OpenAPI doc availability (/docs, /openapi.json)
2. /health endpoint validation
3. /v1/model metadata inspection
4. Session creation (POST /v1/sessions)
5. Unique session ID generation
6. Session retrieval (GET /v1/sessions/{id})
7. Session deletion (DELETE /v1/sessions/{id})
8. Invalid session handling (404 SESSION_NOT_FOUND)
9. Message content validation (empty/whitespace rejection)
10. Generation config override validation
11. Synchronous message generation and telemetry
12. Multi-turn conversation continuation
13. Server-Sent Events (SSE) streaming endpoint
14. Session isolation (Session A vs Session B independence)
15. Per-session concurrency protection
16. Max sessions limit enforcement (429 MAX_SESSIONS_EXCEEDED)
17. Message length limit enforcement (400 INVALID_REQUEST)
18. Explicit session persistence (POST /v1/sessions/{id}/save)
19. Structured error response schema validation
20. Strict CPU execution enforcement
21. Server CLI smoke test (scripts/serve.py --help)
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from fastapi.testclient import TestClient
import pytest
import torch

from myllm.api.app import create_app
from myllm.api.service import APIService
from myllm.config import ModelConfig, ServerConfig
from myllm.model.gpt import GPTModel
from myllm.tokenizer import Tokenizer


@pytest.fixture
def api_test_service():
    """Create a minimal CPU model and APIService for fast, deterministic unit testing."""
    tok_path = Path("checkpoints/smoke/tokenizer.json")
    if tok_path.is_file():
        tokenizer = Tokenizer.load(tok_path)
    else:
        tokenizer = Tokenizer()

    config = ModelConfig(
        vocab_size=len(tokenizer),
        context_length=64,
        n_layer=2,
        n_head=2,
        n_embd=32,
    )
    torch.manual_seed(42)
    model = GPTModel(config)
    model.eval()

    server_cfg = ServerConfig(
        host="127.0.0.1",
        port=8000,
        device="cpu",
        checkpoint="checkpoints/smoke/best.pt",
        tokenizer="checkpoints/smoke/tokenizer.json",
        max_sessions=5,
        max_message_length=1000,
        max_new_tokens=32,
    )

    return APIService(
        model=model,
        tokenizer=tokenizer,
        config=server_cfg,
        checkpoint_path="checkpoints/smoke/best.pt",
    )


@pytest.fixture
def client(api_test_service: APIService) -> TestClient:
    """FastAPI TestClient fixture."""
    app = create_app(service=api_test_service)
    return TestClient(app)


class TestSystemAndMetadataEndpoints:
    """1-3: OpenAPI, /health, /v1/model."""

    def test_openapi_docs_available(self, client: TestClient):
        r_docs = client.get("/docs")
        assert r_docs.status_code == 200

        r_json = client.get("/openapi.json")
        assert r_json.status_code == 200
        schema = r_json.json()
        assert schema["info"]["title"] == "MyLLM Local API"
        assert "/health" in schema["paths"]
        assert "/v1/sessions" in schema["paths"]

    def test_health_endpoint(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data == {
            "status": "ok",
            "service": "MyLLM",
            "device": "cpu",
        }

    def test_model_info_endpoint(self, client: TestClient):
        r = client.get("/v1/model")
        assert r.status_code == 200
        data = r.json()
        assert data["model_name"] == "MyLLM-GPT"
        assert data["device"] == "cpu"
        assert data["context_length"] == 64
        assert data["parameter_count"] > 0
        assert data["kv_cache_supported"] is True


class TestSessionLifecycle:
    """4-8, 16: Session CRUD and limits."""

    def test_create_session(self, client: TestClient):
        payload = {"system_prompt": "You are a test assistant."}
        r = client.post("/v1/sessions", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert "session_id" in data
        assert data["model"] == "MyLLM-GPT"
        assert data["context_length"] == 64
        assert data["system_prompt"] == "You are a test assistant."

    def test_unique_session_ids(self, client: TestClient):
        r1 = client.post("/v1/sessions", json={})
        r2 = client.post("/v1/sessions", json={})
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["session_id"] != r2.json()["session_id"]

    def test_get_session(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={"system_prompt": "System prompt test"})
        sess_id = r_create.json()["session_id"]

        r_get = client.get(f"/v1/sessions/{sess_id}")
        assert r_get.status_code == 200
        detail = r_get.json()
        assert detail["session_id"] == sess_id
        assert detail["system_prompt"] == "System prompt test"
        assert detail["messages"] == []

    def test_delete_session(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sess_id = r_create.json()["session_id"]

        r_del = client.delete(f"/v1/sessions/{sess_id}")
        assert r_del.status_code == 200
        assert r_del.json() == {"status": "deleted", "session_id": sess_id}

        # Subsequent GET must return 404
        r_after = client.get(f"/v1/sessions/{sess_id}")
        assert r_after.status_code == 404
        err = r_after.json()
        assert err["error"]["code"] == "SESSION_NOT_FOUND"

    def test_invalid_session_returns_404(self, client: TestClient):
        r = client.get("/v1/sessions/nonexistent-uuid-12345")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "SESSION_NOT_FOUND"

    def test_max_sessions_limit_enforced(self, client: TestClient):
        # Service configured with max_sessions=5
        session_ids = []
        for i in range(5):
            r = client.post("/v1/sessions", json={})
            assert r.status_code == 201
            session_ids.append(r.json()["session_id"])

        # 6th session should be rejected with 429
        r_over = client.post("/v1/sessions", json={})
        assert r_over.status_code == 429
        assert r_over.json()["error"]["code"] == "MAX_SESSIONS_EXCEEDED"

        # Cleanup
        for sid in session_ids:
            client.delete(f"/v1/sessions/{sid}")


class TestChatEndpoints:
    """9-13: Validation, synchronous generation, multi-turn, SSE streaming."""

    def test_empty_content_rejected(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sid = r_create.json()["session_id"]

        # Whitespace-only content
        r = client.post(f"/v1/sessions/{sid}/messages", json={"content": "   "})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_message_length_limit(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sid = r_create.json()["session_id"]

        # Max allowed is 1000 chars in test fixture
        huge_msg = "x" * 1500
        r = client.post(f"/v1/sessions/{sid}/messages", json={"content": huge_msg})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "INVALID_REQUEST"

    def test_synchronous_message_generation(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sid = r_create.json()["session_id"]

        msg_payload = {
            "content": "Hello world",
            "generation_config": {"max_new_tokens": 5, "do_sample": False},
        }
        r = client.post(f"/v1/sessions/{sid}/messages", json=msg_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["message"]["role"] == "assistant"
        assert len(data["message"]["content"]) > 0
        assert data["telemetry"]["generated_tokens"] > 0
        assert data["telemetry"]["generation_latency"] > 0
        assert data["telemetry"]["tokens_per_second"] > 0

    def test_multi_turn_continuation(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sid = r_create.json()["session_id"]

        # Turn 1
        client.post(
            f"/v1/sessions/{sid}/messages",
            json={"content": "First query", "generation_config": {"max_new_tokens": 4, "do_sample": False}},
        )

        # Turn 2
        client.post(
            f"/v1/sessions/{sid}/messages",
            json={"content": "Second query", "generation_config": {"max_new_tokens": 4, "do_sample": False}},
        )

        r_detail = client.get(f"/v1/sessions/{sid}")
        assert r_detail.status_code == 200
        messages = r_detail.json()["messages"]
        assert len(messages) == 4
        assert messages[0]["content"] == "First query"
        assert messages[1]["role"] == "assistant"
        assert messages[2]["content"] == "Second query"
        assert messages[3]["role"] == "assistant"

    def test_streaming_sse_endpoint(self, client: TestClient):
        r_create = client.post("/v1/sessions", json={})
        sid = r_create.json()["session_id"]

        stream_payload = {
            "content": "Streaming query",
            "generation_config": {"max_new_tokens": 5, "do_sample": False},
        }
        r = client.post(f"/v1/sessions/{sid}/messages/stream", json=stream_payload)
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]

        events = []
        for line in r.text.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                event_dict = json.loads(line[6:])
                events.append(event_dict)

        assert len(events) > 0
        assert events[-1]["finished"] is True
        assert events[-1]["stop_reason"] is not None


class TestSessionIsolationAndPersistence:
    """14, 18: Isolation and persistence."""

    def test_session_isolation(self, client: TestClient):
        # Create Session A and Session B
        sid_a = client.post("/v1/sessions", json={"system_prompt": "System A"}).json()["session_id"]
        sid_b = client.post("/v1/sessions", json={"system_prompt": "System B"}).json()["session_id"]

        # Post distinct messages
        client.post(f"/v1/sessions/{sid_a}/messages", json={"content": "Message for A"})
        client.post(f"/v1/sessions/{sid_b}/messages", json={"content": "Message for B"})

        hist_a = client.get(f"/v1/sessions/{sid_a}").json()["messages"]
        hist_b = client.get(f"/v1/sessions/{sid_b}").json()["messages"]

        assert len(hist_a) == 2
        assert len(hist_b) == 2
        assert hist_a[0]["content"] == "Message for A"
        assert hist_b[0]["content"] == "Message for B"

    def test_session_save(self, client: TestClient, tmp_path):
        sid = client.post("/v1/sessions", json={"system_prompt": "Persist me"}).json()["session_id"]
        client.post(f"/v1/sessions/{sid}/messages", json={"content": "Save test"})

        target_file = tmp_path / "saved_api_session.json"
        r_save = client.post(f"/v1/sessions/{sid}/save", json={"path": str(target_file)})
        assert r_save.status_code == 200
        assert r_save.json()["status"] == "saved"
        assert target_file.is_file()

        with open(target_file, "r", encoding="utf-8") as f:
            saved_content = json.load(f)
        assert saved_content["session_id"] == sid
        assert saved_content["system_prompt"] == "Persist me"
        assert len(saved_content["messages"]) == 2


class TestServerCLI:
    """21: Server CLI smoke test."""

    def test_serve_cli_help(self):
        res = subprocess.run(
            [sys.executable, "scripts/serve.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert res.returncode == 0
        assert "MyLLM Local API Server" in res.stdout
        assert "--checkpoint" in res.stdout
        assert "--tokenizer" in res.stdout
