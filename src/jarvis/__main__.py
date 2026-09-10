"""
CLI & GUI Entry Point for JARVIS local computer assistant.

Supports:
  python -m jarvis [--gui | --cli | --release-check | --doctor | --self-test | --safe-mode | --diagnostic | --version] [command]
"""

import argparse
import sys
import logging
from jarvis.app import JARVISApp
from jarvis.core.diagnostics import JarvisDoctor, JarvisSelfTest, DiagnosticStatus
from jarvis.core.release import JarvisReleaseCheck, ReleaseStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis.cli")


def main():
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS — Local-First Personal AI Desktop Assistant"
    )
    parser.add_argument("--gui", action="store_true", help="Launch Desktop Application (Default)")
    parser.add_argument("--cli", action="store_true", help="Run interactive terminal prompt interface")
    parser.add_argument("--release-check", action="store_true", help="Run production release validation gate")
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

    if args.release_check:
        print("==================================================")
        print("        JARVIS PRODUCTION RELEASE CHECK           ")
        print("==================================================")
        res = JarvisReleaseCheck.run_release_check()
        for check in res["results"]:
            symbol = "[OK]" if check["passed"] else "[FAIL]"
            print(f"{symbol:<6} {check['check']:<25} : {check['message']}")
        print("==================================================")
        print(f"FINAL RELEASE DECISION: {res['status']}")
        if res["blockers"]:
            print("BLOCKERS:")
            for b in res["blockers"]:
                print(f"  - {b}")
        print("==================================================")
        sys.exit(0 if res["is_ready"] else 1)

    if args.doctor:
        print("==================================================")
        print("           JARVIS DOCTOR DIAGNOSTICS             ")
        print("==================================================")
        results = JarvisDoctor.run_diagnostics()
        failed = False
        for res in results:
            symbol = "[OK]" if res.status == DiagnosticStatus.PASS else ("[!]" if res.status == DiagnosticStatus.WARN else "[X]")
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

    # Execute single command if provided
    if args.command:
        app = JARVISApp(safe_mode=args.safe_mode)
        if not app.initialize():
            print("Error initializing JARVIS Application.", file=sys.stderr)
            sys.exit(1)
        cmd_str = " ".join(args.command)
        res = app.execute_command(cmd_str)
        print(res.get("response", res))
        app.shutdown()
        sys.exit(0 if res.get("success") else 1)

    if args.diagnostic:
        import json
        app = JARVISApp(safe_mode=args.safe_mode)
        app.initialize()
        status_report = app.get_system_status()
        print(json.dumps(status_report, indent=2))
        app.shutdown()
        sys.exit(0)

    if args.cli:
        app = JARVISApp(safe_mode=args.safe_mode)
        if not app.initialize():
            sys.exit(1)
        print("==================================================")
        print("  JARVIS Terminal Assistant v0.1.0 Ready (Boss)  ")
        print("  Type 'exit', 'quit', or press Ctrl+C to stop.  ")
        print("==================================================")
        try:
            while True:
                user_input = input("\nBoss > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "shutdown"):
                    break
                result = app.execute_command(user_input)
                print(f"\nJARVIS > {result.get('response', '')}")
        finally:
            app.shutdown()
        sys.exit(0)

    # Default Mode: Launch Desktop GUI
    try:
        from jarvis.ui.desktop_app import JarvisDesktopApp
        desktop_app = JarvisDesktopApp(safe_mode=args.safe_mode)
        exit_code = desktop_app.run()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Error launching Desktop Application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
