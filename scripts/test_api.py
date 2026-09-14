"""
Lightweight API Client Smoke Test for MyLLM Server (Phase 9).

Validates all HTTP and SSE endpoints against a running server:
- /health
- /v1/model
- Session creation, retrieval, and deletion
- Synchronous message generation
- Multi-turn conversation continuation
- Server-Sent Events (SSE) streaming
- Session persistence
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import httpx


def run_smoke_test(base_url: str = "http://127.0.0.1:8000") -> bool:
    print("=" * 65)
    print(f"  MyLLM API Smoke Test Target: {base_url}")
    print("=" * 65)

    client = httpx.Client(base_url=base_url, timeout=30.0)

    try:
        # 1. Health Endpoint
        print("\n[1/9] Testing GET /health ... ", end="", flush=True)
        r = client.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("status") == "ok"
        assert data.get("device") == "cpu"
        print("PASS")

        # 2. Model Info Endpoint
        print("[2/9] Testing GET /v1/model ... ", end="", flush=True)
        r = client.get("/v1/model")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "parameter_count" in data
        assert "context_length" in data
        assert data.get("device") == "cpu"
        print(f"PASS ({data['parameter_count']} params, ctx={data['context_length']})")

        # 3. Create Session
        print("[3/9] Testing POST /v1/sessions ... ", end="", flush=True)
        create_payload = {
            "system_prompt": "You are a concise assistant.",
            "generation_config": {"max_new_tokens": 12, "temperature": 1.0, "do_sample": False},
        }
        r = client.post("/v1/sessions", json=create_payload)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        sess_data = r.json()
        session_id = sess_data["session_id"]
        assert session_id, "Missing session_id in response"
        print(f"PASS (session_id={session_id[:8]}...)")

        # 4. Synchronous Message Generation
        print("[4/9] Testing POST /v1/sessions/{id}/messages (Turn 1) ... ", end="", flush=True)
        msg_payload = {"content": "Hello! What is 2 + 2?"}
        r = client.post(f"/v1/sessions/{session_id}/messages", json=msg_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        resp_data = r.json()
        assert "message" in resp_data
        assert resp_data["message"]["role"] == "assistant"
        assert resp_data["telemetry"]["generated_tokens"] > 0
        ans1 = resp_data["message"]["content"]
        tps = resp_data["telemetry"]["tokens_per_second"]
        print(f"PASS (got '{ans1[:25]}...', {tps:.1f} tok/s)")

        # 5. Multi-Turn Follow-Up Message
        print("[5/9] Testing POST /v1/sessions/{id}/messages (Turn 2 follow-up) ... ", end="", flush=True)
        msg2_payload = {"content": "Can you explain that in one word?"}
        r = client.post(f"/v1/sessions/{session_id}/messages", json=msg2_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        resp2_data = r.json()
        assert resp2_data["message"]["role"] == "assistant"
        print("PASS")

        # 6. Streaming SSE Endpoint
        print("[6/9] Testing POST /v1/sessions/{id}/messages/stream (SSE) ... ", end="", flush=True)
        stream_payload = {"content": "Count to three."}
        events = []
        with client.stream("POST", f"/v1/sessions/{session_id}/messages/stream", json=stream_payload) as stream_resp:
            assert stream_resp.status_code == 200, f"Expected 200, got {stream_resp.status_code}"
            assert "text/event-stream" in stream_resp.headers.get("content-type", "")
            for line in stream_resp.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)

        assert len(events) > 0, "No SSE events received"
        assert events[-1].get("finished") is True, "Last event should be finished=True"
        tokens_received = [e["token"] for e in events if not e.get("finished")]
        print(f"PASS ({len(tokens_received)} stream tokens received)")

        # 7. Get Session Details & History
        print("[7/9] Testing GET /v1/sessions/{id} ... ", end="", flush=True)
        r = client.get(f"/v1/sessions/{session_id}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        detail = r.json()
        assert len(detail["messages"]) >= 4, f"Expected at least 4 messages in history, got {len(detail['messages'])}"
        print(f"PASS (history has {len(detail['messages'])} messages)")

        # 8. Explicit Persistence
        print("[8/9] Testing POST /v1/sessions/{id}/save ... ", end="", flush=True)
        save_payload = {"path": "scratch/api_smoke_session.json"}
        r = client.post(f"/v1/sessions/{session_id}/save", json=save_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        save_data = r.json()
        assert save_data["status"] == "saved"
        print("PASS")

        # 9. Delete Session
        print("[9/9] Testing DELETE /v1/sessions/{id} ... ", end="", flush=True)
        r = client.delete(f"/v1/sessions/{session_id}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

        # Verify session is truly gone
        r_gone = client.get(f"/v1/sessions/{session_id}")
        assert r_gone.status_code == 404, f"Expected 404 after deletion, got {r_gone.status_code}"
        print("PASS (verified 404 on subsequent get)")

        print("\n" + "=" * 65)
        print("  ALL API SMOKE TESTS PASSED (100% SUCCESS)")
        print("=" * 65 + "\n")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM API Smoke Test")
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of the running API server (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    success = run_smoke_test(base_url=args.url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
