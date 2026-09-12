"""
Production Application Bootstrap & Launcher for JARVIS.

Consolidates complete application lifecycle, configuration validation, fast-path
deterministic command execution, lazy subsystem initialization, diagnostic reporting,
and graceful shutdown.
"""

from datetime import datetime
import logging
from pathlib import Path

from typing import Any, Dict, Optional

from jarvis.core.config import JarvisConfig, get_settings, ConfigurationError
from jarvis.core.lifecycle import LifecycleManager, ApplicationState, ApplicationLifecycleError
from jarvis.core.hardware import HardwareDetector, HardwareSpecs
from jarvis.core.capabilities import CapabilityRegistry, CapabilityStatus
from jarvis.memory.database import DatabaseManager
from jarvis.core.orchestration.orchestrator import JarvisOrchestrator, ExecutionStatus
from jarvis.scheduler.manager import SchedulerManager
from jarvis.security.permissions import PermissionEvaluator

logger = logging.getLogger(__name__)


class JARVISApp:
    """
    Main JARVIS Application Controller.
    Single authoritative bootstrap and runtime lifecycle manager.
    """

    def __init__(self, config_path: str = "config/config.yaml", safe_mode: bool = False):
        self.config_path = config_path
        self.safe_mode = safe_mode
        self.lifecycle = LifecycleManager(ApplicationState.CREATED)
        self.hardware_specs: Optional[HardwareSpecs] = None
        self.capabilities = CapabilityRegistry()
        self.config: Optional[JarvisConfig] = None
        
        # Subsystems (lazy or initialized during bootstrap)
        self.db: Optional[DatabaseManager] = None
        self.permission_evaluator: Optional[PermissionEvaluator] = None
        self.orchestrator: Optional[JarvisOrchestrator] = None
        self.scheduler: Optional[SchedulerManager] = None
        self._brain_instance = None
        self._browser_instance = None
        self._voice_instance = None

    def initialize(self) -> bool:
        """Initialize configuration, lifecycle, security, memory, and orchestration components."""
        try:
            self.lifecycle.transition_to(ApplicationState.VALIDATING)
            
            # 1. Load & Validate Configuration
            self.config = get_settings(self.config_path)
            self.config.validate_schema()
            
            # 2. Hardware Detection
            self.hardware_specs = HardwareDetector.detect()
            self._update_hardware_capabilities()
            
            self.lifecycle.transition_to(ApplicationState.INITIALIZING)
            
            # 3. Security & Permission Policy
            perm_file = self.config.security.permissions_file
            if not Path(perm_file).is_absolute():
                perm_file = str(Path(self.config_path).parent / "permissions.yaml")
            self.permission_evaluator = PermissionEvaluator(permissions_file=perm_file)
            
            # 4. Database & Memory Layer
            self.db = DatabaseManager()
            self.capabilities.register("memory", CapabilityStatus.AVAILABLE, "SQLite database connected")

            # 5. Orchestration Pipeline
            self.orchestrator = JarvisOrchestrator()

            # 6. Scheduler Service (unless in safe_mode)
            if not self.safe_mode:
                try:
                    self.scheduler = SchedulerManager(db_manager=self.db, orchestrator=self.orchestrator)
                    self.scheduler.start()
                    self.capabilities.register("scheduler", CapabilityStatus.AVAILABLE, "Background scheduler running")
                except Exception as e:
                    logger.warning(f"Scheduler initialization warning: {e}")
                    self.capabilities.register("scheduler", CapabilityStatus.DEGRADED, f"Scheduler warning: {e}")
            else:
                self.capabilities.register("scheduler", CapabilityStatus.UNAVAILABLE, "Safe mode active - scheduler disabled")

            self.lifecycle.transition_to(ApplicationState.READY)
            logger.info("JARVIS Application initialized successfully and is READY.")
            return True

        except Exception as e:
            logger.error(f"JARVIS Application initialization failed: {e}", exc_info=True)
            self.lifecycle.transition_to(ApplicationState.FAILED)
            return False

    def _update_hardware_capabilities(self) -> None:
        """Update registry capabilities based on hardware detection."""
        if self.hardware_specs:
            if self.hardware_specs.audio_available:
                self.capabilities.register("microphone", CapabilityStatus.AVAILABLE, "Sound hardware detected")
            if self.hardware_specs.browser_available:
                self.capabilities.register("browser", CapabilityStatus.AVAILABLE, "Browser automation ready")
            if self.hardware_specs.ocr_available:
                self.capabilities.register("ocr", CapabilityStatus.AVAILABLE, "OCR engine ready")
            if self.hardware_specs.gpu_available:
                self.capabilities.register("gpu", CapabilityStatus.AVAILABLE, f"GPU: {self.hardware_specs.gpu_device_name}")

    def execute_command(self, user_input: str) -> Dict[str, Any]:
        """
        Main execution pipeline entry point.
        Checks fast-path routes before invoking heavy orchestration.
        """
        if not self.lifecycle.is_ready():
            raise ApplicationLifecycleError(f"Cannot execute command in state {self.lifecycle.state.name}")

        self.lifecycle.transition_to(ApplicationState.RUNNING)
        user_input_strip = user_input.strip()

        try:
            # Check Deterministic Fast-Path
            fast_result = self._try_fast_path(user_input_strip)
            if fast_result is not None:
                self.lifecycle.transition_to(ApplicationState.READY)
                return fast_result

            # Process through Full Orchestrator Pipeline
            if self.orchestrator is None:
                raise RuntimeError("Orchestrator not initialized")

            state = self.orchestrator.handle(user_input_strip)
            success = state.status == ExecutionStatus.COMPLETED
            
            response_text = f"Execution {state.status.value}: {user_input_strip}"
            if state.error:
                response_text = f"Execution failed: {state.error}"
            elif state.observations:
                obs_list = []
                for obs in state.observations:
                    if isinstance(obs, dict) and "output" in obs:
                        obs_list.append(str(obs["output"]))
                    else:
                        obs_list.append(str(obs))
                if obs_list:
                    response_text = "\n".join(obs_list)

            self.lifecycle.transition_to(ApplicationState.READY)
            return {
                "success": success,
                "response": response_text,
                "status": state.status.value,
                "execution_id": state.execution_id,
                "verified": success
            }

        except Exception as e:
            logger.error(f"Error executing command '{user_input_strip}': {e}", exc_info=True)
            self.lifecycle.transition_to(ApplicationState.READY)
            return {
                "success": False,
                "response": f"An error occurred while processing your request: {e}",
                "error": str(e)
            }

    def _try_fast_path(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Fast-path router for deterministic system commands avoiding LLM latency."""
        text_lower = input_text.lower().strip().rstrip(".!?")
        if text_lower.startswith("jarvis,"):
            text_lower = text_lower[7:].strip()
        elif text_lower.startswith("jarvis"):
            text_lower = text_lower[6:].strip()

        # 0. Fast Intent Router
        try:
            from jarvis.brain.fast_path import FastIntentRouter
            match = FastIntentRouter.match(input_text)
            if match.matched:
                if match.target_tool:
                    from jarvis.core.orchestration.dispatcher import ToolDispatcher
                    dispatcher = ToolDispatcher()
                    tool_res = dispatcher.dispatch(match.target_tool, match.parameters)
                    resp_msg = match.fast_response
                    if tool_res.data and isinstance(tool_res.data, dict) and "message" in tool_res.data:
                        resp_msg = tool_res.data["message"]
                    return {
                        "success": tool_res.success,
                        "response": resp_msg,
                        "data": tool_res.data if tool_res.data else {},
                        "fast_path": True,
                        "verified": tool_res.success
                    }
                elif match.fast_response:
                    resp_str = match.fast_response
                    if resp_str == "TIME_QUERY_PLACEHOLDER":
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        resp_str = f"The current time is {now_str}."
                    return {
                        "success": True,
                        "response": resp_str,
                        "data": {},
                        "fast_path": True,
                        "verified": True
                    }
        except Exception as e:
            logger.debug(f"FastIntentRouter check exception: {e}")

        # 1. System Status Check
        if text_lower in (
            "show system status", "system status", "status", "what is system status",
            "what's the current system status?", "what's the current system status",
            "what is the current system status", "current system status", "health", "system health"
        ) or "system status" in text_lower:
            status_report = self.get_system_status()
            return {
                "success": True,
                "response": (
                    f"JARVIS Status: {status_report['lifecycle_state']}\n"
                    f"Performance Mode: {status_report['performance_profile']}\n"
                    f"Available Capabilities: {status_report['capabilities_summary']['available_count']}/"
                    f"{status_report['capabilities_summary']['total_capabilities']}"
                ),
                "data": status_report,
                "fast_path": True,
                "verified": True
            }

        # 2. Time Query
        if text_lower in ("what time is it", "time", "current time", "what is the time"):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {
                "success": True,
                "response": f"The current time is {now_str}.",
                "data": {"time": now_str},
                "fast_path": True,
                "verified": True
            }

        # 3. List Scheduled Tasks
        if text_lower in ("list tasks", "show tasks", "list scheduled tasks", "show scheduled tasks"):
            if self.scheduler:
                tasks = self.scheduler.list_tasks()
                return {
                    "success": True,
                    "response": f"Found {len(tasks)} scheduled tasks.",
                    "data": {"tasks": tasks},
                    "fast_path": True,
                    "verified": True
                }
            return {
                "success": False,
                "response": "Scheduler is unavailable.",
                "fast_path": True,
                "verified": False
            }

        # 4. Read File Fast Path
        if text_lower.startswith("read file ") or text_lower.startswith("read this file "):
            parts = input_text.split("file", 1)
            file_path_str = parts[1].strip() if len(parts) > 1 else ""
            path_obj = Path(file_path_str)
            if path_obj.exists() and path_obj.is_file():
                try:
                    content = path_obj.read_text(encoding="utf-8", errors="replace")
                    return {
                        "success": True,
                        "response": content,
                        "data": {"path": str(path_obj), "content": content},
                        "fast_path": True,
                        "verified": True
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Failed to read file: {e}",
                        "fast_path": True,
                        "verified": False
                    }

        return None

    def get_system_status(self) -> Dict[str, Any]:
        """Comprehensive system status report for --doctor or system.status query."""
        return {
            "application_name": "JARVIS",
            "version": self.config.system.version if self.config else "0.1.0",
            "lifecycle_state": self.lifecycle.state.name,
            "safe_mode": self.safe_mode,
            "hardware_specs": self.hardware_specs.model_dump() if self.hardware_specs else None,
            "performance_profile": self.hardware_specs.performance_profile.value if self.hardware_specs else "UNKNOWN",
            "capabilities_summary": self.capabilities.get_status_report(),
        }

    def shutdown(self) -> None:
        """Gracefully stop background threads, close databases, flush logs."""
        if self.lifecycle.is_stopped():
            return

        logger.info("Initiating JARVIS graceful shutdown...")
        self.lifecycle.transition_to(ApplicationState.STOPPING)

        if self.scheduler:
            try:
                self.scheduler.stop()
            except Exception as e:
                logger.warning(f"Error stopping scheduler: {e}")

        if self.db:
            try:
                self.db.close()
            except Exception as e:
                logger.warning(f"Error closing database: {e}")

        self.lifecycle.transition_to(ApplicationState.STOPPED)
        logger.info("JARVIS Application shutdown complete.")
