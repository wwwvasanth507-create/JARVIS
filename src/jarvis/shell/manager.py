"""
Central Shell Manager orchestrating command validation, execution, process control, and audit logging.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jarvis.security.permissions import RiskLevel
from jarvis.shell.cancellation import JobCanceller
from jarvis.shell.commands import CommandRegistry
from jarvis.shell.environment import ShellEnvironment, ShellInfo
from jarvis.shell.errors import ShellError
from jarvis.shell.executor import ShellExecutor, ShellJob
from jarvis.shell.parser import CommandParser, ParsedCommand
from jarvis.shell.permissions import ShellPermissionChecker
from jarvis.shell.processes import ProcessInfo, ProcessManager
from jarvis.shell.result import AuditRecord, CommandResult
from jarvis.shell.verification import CommandVerifier


class ShellManager:
    """Central entrypoint for safe, permission-controlled, verified terminal operations."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.permission_checker = ShellPermissionChecker(config_path=config_path)
        self.shell_env = ShellEnvironment()
        self.canceller = JobCanceller()
        self.executor = ShellExecutor(environment=self.shell_env, canceller=self.canceller)
        self.process_manager = ProcessManager(canceller=self.canceller)
        self.audit_log: List[AuditRecord] = []

    def _record_audit(
        self,
        tool_name: str,
        parsed: ParsedCommand,
        work_dir: Path,
        risk: RiskLevel,
        allowed: bool,
        confirmed: bool,
        res: Optional[CommandResult] = None,
    ) -> str:
        op_id = f"sh_audit_{uuid.uuid4().hex[:12]}"
        rec = AuditRecord(
            operation_id=op_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            executable=parsed.executable,
            full_command=parsed.raw_command,
            working_directory=str(work_dir.resolve(strict=False)),
            risk_level=risk.value,
            permission_allowed=allowed,
            confirmation_required=(risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)),
            confirmed_by_boss=confirmed,
            exit_code=res.exit_code if res else None,
            status="completed" if (res and res.exit_code == 0) else "failed",
            verified=res.verified if res else False,
        )
        self.audit_log.append(rec)
        return op_id

    def get_shell_info(self) -> ShellInfo:
        """Returns metadata about the current OS platform and shell executable."""
        return self.shell_env.get_shell_info()

    def get_environment(self) -> Dict[str, str]:
        """Returns sanitized environment variables with passwords and tokens redacted."""
        return self.shell_env.get_sanitized_environment()

    def validate_command(
        self,
        command_str: str,
        working_directory: Optional[Union[str, Path]] = None,
    ) -> RiskLevel:
        """Validates command safety without executing."""
        parsed = CommandParser.parse(command_str)
        return self.permission_checker.evaluate_command(parsed, working_directory=working_directory)

    def execute(
        self,
        command_str: str,
        working_directory: Optional[Union[str, Path]] = None,
        timeout: int = 30,
        is_background: bool = False,
        expected_output_pattern: Optional[str] = None,
        expected_artifact_path: Optional[Union[str, Path]] = None,
    ) -> Union[CommandResult, ShellJob]:
        """
        Executes a command through full security evaluation, safety checking, execution, and verification.
        """
        parsed = CommandParser.parse(command_str)
        resolved_dir = self.permission_checker.validator.validate_working_directory(working_directory)
        risk_level = self.permission_checker.evaluate_command(parsed, working_directory=resolved_dir)

        if is_background:
            job = self.executor.start_background_job(
                parsed=parsed,
                working_directory=resolved_dir,
                timeout=timeout,
                risk_level=risk_level,
            )
            self._record_audit(
                tool_name="shell.execute_bg",
                parsed=parsed,
                work_dir=resolved_dir,
                risk=risk_level,
                allowed=True,
                confirmed=True,
            )
            return job

        res = self.executor.execute_sync(
            parsed=parsed,
            working_directory=resolved_dir,
            timeout=timeout,
            risk_level=risk_level,
        )

        res.verified = CommandVerifier.verify_result(
            res,
            expected_output_pattern=expected_output_pattern,
            expected_artifact_path=expected_artifact_path,
        )

        self._record_audit(
            tool_name="shell.execute",
            parsed=parsed,
            work_dir=resolved_dir,
            risk=risk_level,
            allowed=True,
            confirmed=True,
            res=res,
        )

        return res

    def list_processes(self, limit: int = 100) -> List[ProcessInfo]:
        """Lists active system processes."""
        return self.process_manager.list_processes(limit=limit)

    def get_process(self, pid: int) -> ProcessInfo:
        """Inspects single process by PID."""
        return self.process_manager.get_process(pid)

    def terminate_process(self, pid: int, force: bool = False) -> bool:
        """Terminates process by PID safely."""
        parsed = CommandParser.parse(f"terminate_process {pid}")
        resolved_dir = Path(".").resolve(strict=False)
        sec_res = self.permission_checker.security_evaluator.evaluate(
            category="RUN_COMMANDS",
            risk_level=RiskLevel.HIGH,
            action_name="shell.terminate_process",
            parameters={"pid": pid, "force": force},
        )
        if not sec_res.allowed:
            raise ShellError(sec_res.reason)

        success = self.process_manager.terminate_process(pid=pid, force=force)
        self._record_audit(
            tool_name="shell.terminate_process",
            parsed=parsed,
            work_dir=resolved_dir,
            risk=RiskLevel.HIGH,
            allowed=True,
            confirmed=True,
        )
        return success

    def get_job_status(self, job_id: str) -> ShellJob:
        """Retrieves background ShellJob by job_id."""
        return self.executor.get_job(job_id)

    def cancel_job(self, job_id: str) -> ShellJob:
        """Cancels a running background ShellJob."""
        return self.executor.cancel_job(job_id)
