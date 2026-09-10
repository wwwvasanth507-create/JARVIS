"""
CLI Entry Point for JARVIS local computer assistant.

Supports:
  python -m jarvis [--doctor | --self-test | --safe-mode | --diagnostic | --version] [command]
"""

import argparse
import sys
import logging
from jarvis.app import JARVISApp
from jarvis.core.diagnostics import JarvisDoctor, JarvisSelfTest, DiagnosticStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis.cli")


def main():
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS — Local-First Personal AI Desktop Assistant"
    )
    parser.add_argument("--doctor", action="store_true", help="Run comprehensive subsystem diagnostic health check")
    parser.add_argument("--self-test", action="store_true", help="Run safe deterministic end-to-end self-test suite")
    parser.add_argument("--safe-mode", action="store_true", help="Start JARVIS in safe mode (disabled scheduler/risky tools)")
    parser.add_argument("--diagnostic", action="store_true", help="Print detailed hardware specs and capability summary")
    parser.add_argument("--version", action="store_true", help="Display version and exit")
    parser.add_argument("command", nargs="*", help="Optional single command to execute")

    args = parser.parse_args()

    if args.version:
        print("JARVIS Personal Desktop Assistant v0.1.0 (Production Hardened)")
        sys.exit(0)

    if args.doctor:
        print("==================================================")
        print("           JARVIS DOCTOR DIAGNOSTICS             ")
        print("==================================================")
        results = JarvisDoctor.run_diagnostics()
        failed = False
        for res in results:
            symbol = "✓" if res.status == DiagnosticStatus.PASS else ("!" if res.status == DiagnosticStatus.WARN else "✗")
            print(f"[{res.status.value:<4}] {symbol} {res.component:<25} : {res.message}")
            if res.status == DiagnosticStatus.FAIL:
                failed = True
        print("==================================================")
        sys.exit(1 if failed else 0)

    if args.self-test:
        print("==================================================")
        print("           JARVIS SELF-TEST SUITE                ")
        print("==================================================")
        report = JarvisSelfTest.run_self_test()
        for test_name, status in report["tests"].items():
            print(f"  {test_name:<30} : {status}")
        print(f"Overall Self-Test Result: {report['overall_status']}")
        print("==================================================")
        sys.exit(0 if report['overall_status'] == "PASS" else 1)

    app = JARVISApp(safe_mode=args.safe_mode)
    if not app.initialize():
        print("Error initializing JARVIS Application.", file=sys.stderr)
        sys.exit(1)

    if args.diagnostic:
        import json
        status_report = app.get_system_status()
        print(json.dumps(status_report, indent=2))
        app.shutdown()
        sys.exit(0)

    # Execute single command if provided
    if args.command:
        cmd_str = " ".join(args.command)
        res = app.execute_command(cmd_str)
        print(res.get("response", res))
        app.shutdown()
        sys.exit(0 if res.get("success") else 1)

    # Interactive Loop if run without command
    print("==================================================")
    print("  JARVIS Desktop Assistant v0.1.0 Ready (Boss)   ")
    print("  Type 'exit', 'quit', or press Ctrl+C to stop.  ")
    print("==================================================")
    
    try:
        while True:
            try:
                user_input = input("\nBoss > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "shutdown"):
                    print("Shutting down JARVIS...")
                    break
                result = app.execute_command(user_input)
                print(f"\nJARVIS > {result.get('response', '')}")
            except (KeyboardInterrupt, EOFError):
                print("\nReceived exit signal.")
                break
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
