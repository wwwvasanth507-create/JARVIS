"""
Subprocess execution, output stream capping, timeout management, and background job lifecycle engine.
"""

import os
import shutil
import subprocess
import time
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from jarvis.security.permissions import RiskLevel
from jarvis.shell.cancellation import JobCanceller
from jarvis.shell.environment import ShellEnvironment
from jarvis.shell.errors import CommandTimedOut, JobNotFound, OutputTruncated
from jarvis.shell.parser import ParsedCommand
from jarvis.shell.result import CommandRequest, CommandResult


class ShellJob(BaseModel):
    job_id: str
    command: str
    arguments: List[str]
    working_directory: str
    status: str  # QUEUED, RUNNING, COMPLETED, FAILED, TIMED_OUT, CANCELLED
    start_time: str
    end_time: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    truncated: bool = False


class ShellExecutor:
    """Handles synchronous and background subprocess execution with safety bounds."""

    def __init__(
        self,
        environment: Optional[ShellEnvironment] = None,
        canceller: Optional[JobCanceller] = None,
        max_stdout_bytes: int = 524288,
        max_stderr_bytes: int = 524288,
        max_output_lines: int = 2000,
        max_concurrent_jobs: int = 5,
    ):
        self.env = environment or ShellEnvironment()
        self.canceller = canceller or JobCanceller()
        self.max_stdout_bytes = max_stdout_bytes
        self.max_stderr_bytes = max_stderr_bytes
        self.max_output_lines = max_output_lines
        self.max_concurrent_jobs = max_concurrent_jobs

        self._background_jobs: Dict[str, ShellJob] = {}
        self._job_threads: Dict[str, threading.Thread] = {}

    def _truncate_output(self, text: str, max_bytes: int) -> tuple[str, bool]:
        """Truncates output string if it exceeds max_bytes or line bounds."""
        encoded = text.encode("utf-8", errors="replace")
        truncated = False
        if len(encoded) > max_bytes:
            encoded = encoded[:max_bytes]
            text = encoded.decode("utf-8", errors="ignore")
            truncated = True

        lines = text.splitlines()
        if len(lines) > self.max_output_lines:
            text = "\n".join(lines[: self.max_output_lines])
            truncated = True

        return text, truncated

    def execute_sync(
        self,
        parsed: ParsedCommand,
        working_directory: Path,
        timeout: int = 30,
        env_overrides: Optional[Dict[str, str]] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> CommandResult:
        """Executes a command synchronously within timeout and resource limits."""
        start_time = time.time()
        job_id = f"cmd_{uuid.uuid4().hex[:12]}"

        # Merge environment safely
        proc_env = dict(os.environ)
        if env_overrides:
            proc_env.update(env_overrides)

        # Form argument array
        cmd_args = [parsed.executable] + parsed.arguments if parsed.arguments else [parsed.executable]

        # Use shell=True if pipeline operator, shell builtin, or executable not on PATH
        is_builtin = parsed.executable.lower() in {"echo", "dir", "ver", "pwd", "cls", "set", "type"}
        use_shell = parsed.has_pipeline_operators or is_builtin or (shutil.which(parsed.executable) is None)

        try:
            if use_shell:
                proc = subprocess.Popen(
                    parsed.raw_command,
                    shell=True,
                    cwd=working_directory,
                    env=proc_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            else:
                proc = subprocess.Popen(
                    cmd_args,
                    shell=False,
                    cwd=working_directory,
                    env=proc_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            self.canceller.register_process(job_id, proc)

            try:
                stdout_raw, stderr_raw = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.canceller.cancel_job(job_id)
                stdout_raw, stderr_raw = proc.communicate()
                duration = (time.time() - start_time) * 1000.0
                return CommandResult(
                    command=parsed.raw_command,
                    arguments=parsed.arguments,
                    working_directory=str(working_directory),
                    exit_code=-1,
                    stdout=stdout_raw or "",
                    stderr=stderr_raw or f"Execution timed out after {timeout} seconds.",
                    duration_ms=duration,
                    timed_out=True,
                    cancelled=False,
                    verified=False,
                    truncated=False,
                    risk_level=risk_level,
                )
            finally:
                self.canceller.unregister_process(job_id)

            duration = (time.time() - start_time) * 1000.0

            clean_stdout, trunc_out = self._truncate_output(stdout_raw or "", self.max_stdout_bytes)
            clean_stderr, trunc_err = self._truncate_output(stderr_raw or "", self.max_stderr_bytes)

            return CommandResult(
                command=parsed.raw_command,
                arguments=parsed.arguments,
                working_directory=str(working_directory),
                exit_code=proc.returncode,
                stdout=clean_stdout,
                stderr=clean_stderr,
                duration_ms=duration,
                timed_out=False,
                cancelled=False,
                verified=False,
                truncated=(trunc_out or trunc_err),
                risk_level=risk_level,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000.0
            return CommandResult(
                command=parsed.raw_command,
                arguments=parsed.arguments,
                working_directory=str(working_directory),
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                duration_ms=duration,
                timed_out=False,
                cancelled=False,
                verified=False,
                truncated=False,
                risk_level=risk_level,
            )

    def start_background_job(
        self,
        parsed: ParsedCommand,
        working_directory: Path,
        timeout: int = 3600,
        env_overrides: Optional[Dict[str, str]] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> ShellJob:
        """Starts a command in a background thread and tracks its ShellJob state."""
        # Prune finished jobs count
        active_count = sum(1 for j in self._background_jobs.values() if j.status == "RUNNING")
        if active_count >= self.max_concurrent_jobs:
            raise ValueError(f"Max concurrent background jobs ({self.max_concurrent_jobs}) reached.")

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        job = ShellJob(
            job_id=job_id,
            command=parsed.raw_command,
            arguments=parsed.arguments,
            working_directory=str(working_directory),
            status="RUNNING",
            start_time=now_str,
        )
        self._background_jobs[job_id] = job

        def runner():
            res = self.execute_sync(
                parsed=parsed,
                working_directory=working_directory,
                timeout=timeout,
                env_overrides=env_overrides,
                risk_level=risk_level,
            )
            job.end_time = datetime.now(timezone.utc).isoformat()
            job.exit_code = res.exit_code
            job.stdout = res.stdout
            job.stderr = res.stderr
            job.duration_ms = res.duration_ms
            job.truncated = res.truncated

            if res.timed_out:
                job.status = "TIMED_OUT"
            elif res.cancelled:
                job.status = "CANCELLED"
            elif res.exit_code == 0:
                job.status = "COMPLETED"
            else:
                job.status = "FAILED"

        t = threading.Thread(target=runner, daemon=True)
        self._job_threads[job_id] = t
        t.start()

        return job

    def get_job(self, job_id: str) -> ShellJob:
        """Retrieves ShellJob state by job_id."""
        if job_id not in self._background_jobs:
            raise JobNotFound(f"Background job '{job_id}' not found.")
        return self._background_jobs[job_id]

    def cancel_job(self, job_id: str) -> ShellJob:
        """Cancels a background job."""
        job = self.get_job(job_id)
        if job.status == "RUNNING":
            self.canceller.cancel_job(job_id)
            job.status = "CANCELLED"
            job.end_time = datetime.now(timezone.utc).isoformat()
        return job
