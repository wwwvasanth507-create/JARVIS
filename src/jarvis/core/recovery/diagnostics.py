"""
Deterministic Diagnostic Engine for JARVIS recovery.
Executes cheap, deterministic subsystem diagnostic checks to verify state and root causes.
"""

import os
import logging
from typing import Any, Dict, Optional
from jarvis.core.recovery.evidence import DiagnosticEvidence, EvidenceCollector
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause

logger = logging.getLogger("jarvis.core.recovery.diagnostics")


class DiagnosticEngine:
    """Performs deterministic subsystem diagnostics without calling expensive VLM/LLMs."""

    def diagnose(self, event: FailureEvent) -> Tuple[RootCause, DiagnosticEvidence]:
        """
        Runs deterministic diagnostic routines based on failure event details.
        """
        evidence = DiagnosticEvidence()
        tool = event.tool_name.lower()
        args = event.arguments_summary

        # 1. Resource check
        evidence.resource_state = EvidenceCollector.collect_resource_state()

        # 2. Filesystem diagnostics
        if "file" in tool or "path" in str(args).lower() or "file" in str(args).lower():
            target_path = args.get("path") or args.get("source") or args.get("file_path") or args.get("destination")
            if isinstance(target_path, str):
                evidence.filesystem_state = EvidenceCollector.collect_filesystem_evidence(target_path)

        # 3. Shell diagnostics
        if "shell" in tool or "command" in str(args).lower():
            stderr = event.verification_result.get("stderr") or event.error_message
            exit_code = event.verification_result.get("exit_code")
            evidence.shell_state = EvidenceCollector.collect_shell_evidence(stderr=stderr, exit_code=exit_code)

        # Build RootCause with diagnostic evidence
        root_cause = self._evaluate_root_cause(event, evidence)
        return root_cause, evidence

    def _evaluate_root_cause(self, event: FailureEvent, evidence: DiagnosticEvidence) -> RootCause:
        """Determines refined root cause using collected evidence."""
        # Check path evidence
        if evidence.filesystem_state and not evidence.filesystem_state.get("exists", True):
            path = evidence.filesystem_state.get("path", "specified path")
            return RootCause(
                category=FailureCategory.PATH_INVALID,
                confidence=ConfidenceLevel.LIKELY,
                evidence=evidence.filesystem_state,
                likely_causes=[f"Target path '{path}' does not exist on local filesystem"],
            )

        # Check shell evidence
        if evidence.shell_state and evidence.shell_state.get("is_timeout"):
            return RootCause(
                category=FailureCategory.TIMEOUT,
                confidence=ConfidenceLevel.LIKELY,
                evidence=evidence.shell_state,
                likely_causes=["Terminal command exceeded execution timeout limit"],
            )

        # Check resource overload
        if evidence.resource_state:
            ram_avail = evidence.resource_state.get("ram_available_mb", 1000)
            if ram_avail < 200:
                return RootCause(
                    category=FailureCategory.RESOURCE_UNAVAILABLE,
                    confidence=ConfidenceLevel.POSSIBLE,
                    evidence=evidence.resource_state,
                    likely_causes=[f"System memory low ({ram_avail} MB available)"],
                )

        # Default classification
        return RootCause(
            category=event.failure_type or FailureCategory.UNKNOWN,
            confidence=ConfidenceLevel.POSSIBLE,
            evidence={"error": event.error_message},
            likely_causes=[event.error_message or "Subsystem execution failure"],
        )
