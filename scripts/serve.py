"""
Local API Server Launcher for MyLLM (Phase 9).

Launches the FastAPI ASGI application on CPU via Uvicorn.
Provides REST and SSE endpoints for local conversational inference.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import uvicorn

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from myllm.api.app import create_app
from myllm.api.service import APIService
from myllm.config import ServerConfig
from myllm.utils.device import resolve_device


def print_server_banner(service: APIService, host: str, port: int) -> None:
    """Display startup information."""
    print("=" * 65)
    print("  MyLLM Local API Server (CPU-Only)")
    print("=" * 65)
    print(f"  Service Address  : http://{host}:{port}")
    print(f"  API Docs         : http://{host}:{port}/docs")
    print(f"  OpenAPI Schema   : http://{host}:{port}/openapi.json")
    print(f"  Model Checkpoint : {service.checkpoint_path}")
    print(f"  Context Length   : {service.context_length} tokens")
    print(f"  Parameters       : {service.parameter_count:,}")
    print(f"  Device           : {service.device.type.upper()} (Strict CPU)")
    print(f"  Max Sessions     : {service.config.max_sessions}")
    print("=" * 65)
    print("  Available Endpoints:")
    print("    GET    /health")
    print("    GET    /ready")
    print("    GET    /v1/model")
    print("    POST   /v1/sessions")
    print("    GET    /v1/sessions/{id}")
    print("    DELETE /v1/sessions/{id}")
    print("    POST   /v1/sessions/{id}/messages")
    print("    POST   /v1/sessions/{id}/messages/stream")
    print("    POST   /v1/sessions/{id}/save")
    print("=" * 65)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Local API Server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/efficient_sft/checkpoints/best.pt",
        help="Path to trained model checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer.json",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Compute device (strictly 'cpu')",
    )
    parser.add_argument(
        "--max-sessions",
        type=int,
        default=100,
        help="Maximum concurrent active sessions (default: 100)",
    )

    args = parser.parse_args()

    # Enforce CPU execution
    resolve_device(args.device, strict_cpu=True)

    server_config = ServerConfig(
        host=args.host,
        port=args.port,
        device=args.device,
        checkpoint=args.checkpoint,
        tokenizer=args.tokenizer,
        max_sessions=args.max_sessions,
    )

    # Initialize Service and Application
    try:
        service = APIService.create_from_config(server_config)
    except Exception as e:
        print(f"Error initializing MyLLM API Service: {e}", file=sys.stderr)
        sys.exit(1)

    app = create_app(service=service, config=server_config)

    print_server_banner(service, args.host, args.port)

    if args.host == "0.0.0.0":
        print("!" * 65)
        print("  SECURITY WARNING: Server is binding to 0.0.0.0 (all interfaces).")
        print("  MyLLM provides NO authentication, NO authorization, and NO TLS.")
        print("  This server is NOT intended for public internet exposure.")
        print("!" * 65)
        print()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
