"""
Release Validation and Production Gate Engine for JARVIS.

Provides `jarvis --release-check` functionality to verify all release requirements
before distribution.
"""

from enum import Enum
from pathlib import Path
import logging
from typing import Dict, Any, List

from jarvis.core.config import get_settings
from jarvis.core.diagnostics import JarvisDoctor, JarvisSelfTest, DiagnosticStatus
from jarvis.core.hardware import HardwareDetector

logger = logging.getLogger(__name__)


class ReleaseStatus(str, Enum):
    READY = "RELEASE READY"
    BLOCKED = "RELEASE BLOCKED"


class ReleaseCheckResult:
    def __init__(self, check_name: str, passed: bool, message: str):
        self.check_name = check_name
        self.passed = passed
        self.message = message


class JarvisReleaseCheck:
    """Evaluates release criteria and produces a production readiness decision."""

    @classmethod
    def run_release_check(cls) -> Dict[str, Any]:
        results: List[ReleaseCheckResult] = []
        blockers: List[str] = []

        # 1. Package Metadata Check
        try:
            pyproject = Path("pyproject.toml")
            if pyproject.exists() and "name = \"jarvis-agent\"" in pyproject.read_text(encoding="utf-8"):
                results.append(ReleaseCheckResult("Package Metadata", True, "pyproject.toml valid and versioned"))
            else:
                results.append(ReleaseCheckResult("Package Metadata", False, "pyproject.toml missing or invalid"))
                blockers.append("Invalid pyproject.toml package metadata")
        except Exception as e:
            results.append(ReleaseCheckResult("Package Metadata", False, str(e)))
            blockers.append(f"Package metadata error: {e}")

        # 2. Runtime & App Importability
        try:
            import jarvis.app
            import jarvis.core.lifecycle
            import jarvis.core.hardware
            results.append(ReleaseCheckResult("Core Runtime Imports", True, "All core runtime packages importable"))
        except ImportError as e:
            results.append(ReleaseCheckResult("Core Runtime Imports", False, str(e)))
            blockers.append(f"Core import failure: {e}")

        # 3. Desktop UI Importability
        try:
            import jarvis.ui.desktop_app
            import jarvis.ui.theme
            results.append(ReleaseCheckResult("Desktop UI Imports", True, "All UI desktop packages importable"))
        except ImportError as e:
            results.append(ReleaseCheckResult("Desktop UI Imports", False, str(e)))
            blockers.append(f"UI import failure: {e}")

        # 4. Configuration Schema Validation
        try:
            cfg = get_settings()
            cfg.validate_schema()
            results.append(ReleaseCheckResult("Configuration Validation", True, "config.yaml schema valid"))
        except Exception as e:
            results.append(ReleaseCheckResult("Configuration Validation", False, str(e)))
            blockers.append(f"Configuration error: {e}")

        # 5. Doctor Health Suite Check
        try:
            doctor_res = JarvisDoctor.run_diagnostics()
            fails = [r for r in doctor_res if r.status == DiagnosticStatus.FAIL]
            if not fails:
                results.append(ReleaseCheckResult("Subsystem Doctor", True, f"All {len(doctor_res)} diagnostic checks passed/warned"))
            else:
                results.append(ReleaseCheckResult("Subsystem Doctor", False, f"{len(fails)} diagnostic checks failed"))
                blockers.append(f"{len(fails)} diagnostic doctor checks failed")
        except Exception as e:
            results.append(ReleaseCheckResult("Subsystem Doctor", False, str(e)))
            blockers.append(f"Doctor failure: {e}")

        # 6. Self-Test Suite
        try:
            st = JarvisSelfTest.run_self_test()
            if st["overall_status"] == "PASS":
                results.append(ReleaseCheckResult("Self-Test Verification", True, "Safe end-to-end self-test suite passed"))
            else:
                results.append(ReleaseCheckResult("Self-Test Verification", False, "Self-test failed"))
                blockers.append("Self-test suite failed")
        except Exception as e:
            results.append(ReleaseCheckResult("Self-Test Verification", False, str(e)))
            blockers.append(f"Self-test error: {e}")

        # 7. Test Discovery Check
        try:
            test_dir = Path("tests")
            test_files = list(test_dir.glob("**/*.py"))
            if len(test_files) > 10:
                results.append(ReleaseCheckResult("Test Suite Discovery", True, f"Found {len(test_files)} test module files"))
            else:
                results.append(ReleaseCheckResult("Test Suite Discovery", False, f"Only found {len(test_files)} test files"))
                blockers.append("Insufficient test files discovered")
        except Exception as e:
            results.append(ReleaseCheckResult("Test Suite Discovery", False, str(e)))
            blockers.append(f"Test discovery error: {e}")

        is_ready = len(blockers) == 0
        overall_status = ReleaseStatus.READY if is_ready else ReleaseStatus.BLOCKED

        return {
            "status": overall_status.value,
            "is_ready": is_ready,
            "check_count": len(results),
            "blocker_count": len(blockers),
            "blockers": blockers,
            "results": [
                {"check": r.check_name, "passed": r.passed, "message": r.message}
                for r in results
            ]
        }
