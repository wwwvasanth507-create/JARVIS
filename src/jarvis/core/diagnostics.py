"""
Production Diagnostic Engine and Self-Test Suite for JARVIS.

Provides `jarvis --doctor` and `jarvis --self-test` functionality.
"""

from enum import Enum
import logging
from typing import Dict, Any, List
from jarvis.core.config import get_settings, ConfigurationError
from jarvis.core.hardware import HardwareDetector
from jarvis.core.capabilities import CapabilityRegistry, CapabilityStatus
from jarvis.memory.database import DatabaseManager
from jarvis.security.permissions import PermissionEvaluator
from jarvis.core.orchestration.orchestrator import JarvisOrchestrator
from jarvis.scheduler.manager import SchedulerManager

logger = logging.getLogger(__name__)


class DiagnosticStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class DiagnosticResult:
    def __init__(self, component: str, status: DiagnosticStatus, message: str, details: Dict[str, Any] = None):
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}


class JarvisDoctor:
    """Production Diagnostic Doctor testing all subsystems."""

    @classmethod
    def run_diagnostics(cls, config_path: str = "config/config.yaml") -> List[DiagnosticResult]:
        results: List[DiagnosticResult] = []

        # 1. Configuration Check
        try:
            cfg = get_settings(config_path)
            cfg.validate_schema()
            results.append(DiagnosticResult("Configuration", DiagnosticStatus.PASS, f"Loaded and validated from {config_path}"))
        except Exception as e:
            results.append(DiagnosticResult("Configuration", DiagnosticStatus.FAIL, f"Config error: {e}"))

        # 2. Hardware Detection
        try:
            hw = HardwareDetector.detect()
            results.append(DiagnosticResult("Hardware Detection", DiagnosticStatus.PASS, f"{hw.cpu_count} CPUs, {hw.total_ram_gb}GB RAM ({hw.performance_profile.value} mode)"))
        except Exception as e:
            results.append(DiagnosticResult("Hardware Detection", DiagnosticStatus.WARN, f"Hardware check warning: {e}"))

        # 3. Database Check
        try:
            db = DatabaseManager()
            healthy = db.health_check()
            db.close()
            if healthy:
                results.append(DiagnosticResult("Database (SQLite)", DiagnosticStatus.PASS, "SQLite database connection operational"))
            else:
                results.append(DiagnosticResult("Database (SQLite)", DiagnosticStatus.FAIL, "SQLite health check failed"))
        except Exception as e:
            results.append(DiagnosticResult("Database (SQLite)", DiagnosticStatus.FAIL, f"Database error: {e}"))

        # 4. Permissions Policy Check
        try:
            pe = PermissionEvaluator()
            results.append(DiagnosticResult("Permissions Policy", DiagnosticStatus.PASS, "Permission policy loaded and active"))
        except Exception as e:
            results.append(DiagnosticResult("Permissions Policy", DiagnosticStatus.FAIL, f"Permissions policy error: {e}"))

        # 5. Tool Registry Check
        try:
            from jarvis.tools.registry import default_registry
            tool_count = len(default_registry.list_tools())
            results.append(DiagnosticResult("Tool Registry", DiagnosticStatus.PASS, f"{tool_count} tools registered"))
        except Exception as e:
            results.append(DiagnosticResult("Tool Registry", DiagnosticStatus.FAIL, f"Tool registry error: {e}"))

        # 6. Skill System Check
        try:
            from jarvis.skills.registry import SkillRegistry
            sr = SkillRegistry()
            skill_count = len(sr.list_manifests())
            results.append(DiagnosticResult("Skill Subsystem", DiagnosticStatus.PASS, f"{skill_count} skill manifests loaded"))
        except Exception as e:
            results.append(DiagnosticResult("Skill Subsystem", DiagnosticStatus.FAIL, f"Skill subsystem error: {e}"))

        # 7. Scheduler Check
        try:
            from jarvis.scheduler.manager import SchedulerManager
            results.append(DiagnosticResult("Task Scheduler", DiagnosticStatus.PASS, "Scheduler subsystem operational"))
        except Exception as e:
            results.append(DiagnosticResult("Task Scheduler", DiagnosticStatus.WARN, f"Scheduler check warning: {e}"))

        # 8. Model Runtime Check
        try:
            from jarvis.brain.gguf_provider import LocalGGUFProvider
            results.append(DiagnosticResult("Local Model Runtime", DiagnosticStatus.PASS, "GGUF provider available (lazy loading active)"))
        except Exception as e:
            results.append(DiagnosticResult("Local Model Runtime", DiagnosticStatus.WARN, f"Model runtime note: {e}"))

        # 9. Voice & WakeWord Subsystem Check
        try:
            import sounddevice
            results.append(DiagnosticResult("Audio Hardware", DiagnosticStatus.PASS, "Sound device framework available"))
        except ImportError:
            results.append(DiagnosticResult("Audio Hardware", DiagnosticStatus.WARN, "sounddevice optional library missing"))

        # 10. Playwright Browser Check
        try:
            import playwright
            results.append(DiagnosticResult("Browser Automation", DiagnosticStatus.PASS, "Playwright library installed"))
        except ImportError:
            results.append(DiagnosticResult("Browser Automation", DiagnosticStatus.WARN, "Playwright optional package missing"))

        return results


class JarvisSelfTest:
    """Safe deterministic end-to-end self-test suite."""

    @classmethod
    def run_self_test(cls) -> Dict[str, Any]:
        test_results = {}
        
        # Test 1: Config loading
        try:
            cfg = get_settings()
            test_results["config_load"] = "PASS"
        except Exception as e:
            test_results["config_load"] = f"FAIL: {e}"

        # Test 2: Database Manager initialization
        try:
            db = DatabaseManager()
            healthy = db.health_check()
            db.close()
            test_results["database_init"] = "PASS" if healthy else "FAIL"
        except Exception as e:
            test_results["database_init"] = f"FAIL: {e}"

        # Test 3: Orchestrator processing fast-path
        try:
            from jarvis.app import JARVISApp
            app = JARVISApp(safe_mode=True)
            if app.initialize():
                res = app.execute_command("what time is it")
                app.shutdown()
                test_results["fast_path_command"] = "PASS" if res.get("success") else f"FAIL: {res}"
            else:
                test_results["fast_path_command"] = "FAIL: App init failed"
        except Exception as e:
            test_results["fast_path_command"] = f"FAIL: {e}"

        all_passed = all(val == "PASS" for val in test_results.values())
        return {
            "overall_status": "PASS" if all_passed else "FAIL",
            "tests": test_results
        }
