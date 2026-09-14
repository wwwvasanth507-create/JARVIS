#!/usr/bin/env python3
"""
Single-Command Local Launcher for MyLLM.

Orchestrates:
1. Environment and CPU validation
2. Model artifact verification
3. Starting the FastAPI ASGI server
4. Optionally launching the Vite frontend development server
5. Graceful process management and clean termination on Ctrl+C
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_diagnostics() -> bool:
    """Run environment check and return True if successful."""
    print("[1/3] Running environment and CPU diagnostics...")
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "check_environment.py")]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return res.returncode == 0


def run_verification(checkpoint: str, tokenizer: str) -> bool:
    """Verify model artifact before launching."""
    print("\n[2/3] Verifying model artifact and checksums...")
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "verify_model.py"),
        "--checkpoint", checkpoint,
        "--tokenizer", tokenizer,
    ]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return res.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="MyLLM Local Application Launcher")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface for API server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API server (default: 8000)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=5173,
        help="Port for Frontend dev server (default: 5173)",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="experiments/phase7/phase7_sft_run/checkpoints/best.pt",
        help="Path to model checkpoint",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default="data/tokenized/tokenizer.json",
        help="Path to tokenizer.json",
    )
    parser.add_argument(
        "--with-frontend",
        action="store_true",
        default=False,
        help="Also start the Vite frontend development server",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        default=False,
        help="Skip pre-flight model verification",
    )
    args = parser.parse_args()

    # Step 1: Environment Check
    if not run_diagnostics():
        print("Launcher aborted: Environment diagnostics failed.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Model Verification
    if not args.skip_verify:
        if not run_verification(args.checkpoint, args.tokenizer):
            print("Launcher aborted: Model artifact verification failed.", file=sys.stderr)
            sys.exit(1)

    # Step 3: Launch Services
    print("\n[3/3] Starting MyLLM local services...")
    api_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "serve.py"),
        "--host", args.host,
        "--port", str(args.port),
        "--checkpoint", args.checkpoint,
        "--tokenizer", args.tokenizer,
    ]

    processes: list[subprocess.Popen] = []

    try:
        print(f"  Starting FastAPI server on http://{args.host}:{args.port} ...")
        api_proc = subprocess.Popen(api_cmd, cwd=str(REPO_ROOT))
        processes.append(api_proc)

        fe_proc = None
        if args.with_frontend:
            npm_bin = shutil.which("npm")
            fe_dir = REPO_ROOT / "frontend"
            if npm_bin and (fe_dir / "node_modules").is_dir():
                print(f"  Starting Frontend Web UI on http://localhost:{args.frontend_port} ...")
                # On Windows, npm is a batch script
                fe_cmd = f"npm run dev -- --host 127.0.0.1 --port {args.frontend_port}"
                fe_proc = subprocess.Popen(fe_cmd, cwd=str(fe_dir), shell=True)
                processes.append(fe_proc)
            else:
                print("  Note: Frontend dependencies not detected. Run 'cd frontend && npm install'.")

        print("\n" + "=" * 65)
        print("  MyLLM Local Application Running")
        print(f"  Backend API    : http://{args.host}:{args.port}")
        print(f"  API Docs       : http://{args.host}:{args.port}/docs")
        print(f"  Readiness      : http://{args.host}:{args.port}/ready")
        if fe_proc:
            print(f"  Web UI         : http://localhost:{args.frontend_port}")
        else:
            print(f"  Web UI Command : cd frontend && npm run dev")
        print("  Press Ctrl+C to stop all services cleanly.")
        print("=" * 65 + "\n")

        # Monitor processes
        while True:
            for p in processes:
                code = p.poll()
                if code is not None:
                    print(f"A service terminated with exit code {code}.")
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping MyLLM services...")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("All services stopped cleanly.")


if __name__ == "__main__":
    main()
