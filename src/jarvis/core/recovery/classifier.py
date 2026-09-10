"""
Failure Classifier for JARVIS recovery.
Maps errors, observations, and tool parameters to FailureCategory and initial RootCause.
"""

from typing import Any, Dict, Optional
from jarvis.core.recovery.failure import FailureCategory, FailureEvent
from jarvis.core.recovery.root_cause import ConfidenceLevel, RootCause


class FailureClassifier:
    """Classifies tool execution failures into standardized failure categories."""

    def classify(self, event: FailureEvent) -> RootCause:
        err_msg = (event.error_message or "").lower()
        tool = event.tool_name.lower()

        # 1. PERMISSION_DENIED
        if "permission denied" in err_msg or "unauthorized" in err_msg or "blocked by policy" in err_msg:
            return RootCause(
                category=FailureCategory.PERMISSION_DENIED,
                confidence=ConfidenceLevel.LIKELY,
                evidence={"error": event.error_message},
                likely_causes=["Action violates security policy or permissions.yaml restrictions"],
            )

        # 2. TIMEOUT
        if "timeout" in err_msg or "timed out" in err_msg or event.error_code == "TIMEOUT":
            return RootCause(
                category=FailureCategory.TIMEOUT,
                confidence=ConfidenceLevel.LIKELY,
                evidence={"error": event.error_message},
                likely_causes=["Subsystem or remote target took too long to respond"],
            )

        # 3. APPLICATION_NOT_READY
        if "app" in tool or "application" in tool:
            if "not running" in err_msg or "not found" in err_msg or "failed to launch" in err_msg:
                return RootCause(
                    category=FailureCategory.APPLICATION_NOT_READY,
                    confidence=ConfidenceLevel.LIKELY,
                    evidence={"tool": event.tool_name, "error": event.error_message},
                    likely_causes=["Application executable missing, crash, or launch delay"],
                )

        # 4. VISUAL_TARGET_NOT_FOUND
        if "screen" in tool or "vision" in tool or "visual" in err_msg:
            if "target not found" in err_msg or "not visible" in err_msg:
                return RootCause(
                    category=FailureCategory.VISUAL_TARGET_NOT_FOUND,
                    confidence=ConfidenceLevel.LIKELY,
                    evidence={"tool": event.tool_name, "error": event.error_message},
                    likely_causes=["UI target moved, window hidden, or OCR mismatch"],
                )

        # 5. NOT_FOUND / PATH_INVALID
        if "file" in tool or "filesystem" in tool or "path" in err_msg or "not found" in err_msg:
            if "path" in err_msg or "no such file" in err_msg or "does not exist" in err_msg:
                return RootCause(
                    category=FailureCategory.PATH_INVALID,
                    confidence=ConfidenceLevel.LIKELY,
                    evidence={"tool": event.tool_name, "error": event.error_message},
                    likely_causes=["Target file or directory path does not exist"],
                )

        # 6. VERIFICATION_FAILED
        if "verification" in err_msg or "post-condition" in err_msg:
            return RootCause(
                category=FailureCategory.VERIFICATION_FAILED,
                confidence=ConfidenceLevel.LIKELY,
                evidence={"verification": event.verification_result},
                likely_causes=["Tool executed but expected system state change was not observed"],
            )

        # Fallback UNKNOWN
        return RootCause(
            category=FailureCategory.UNKNOWN,
            confidence=ConfidenceLevel.POSSIBLE,
            evidence={"error": event.error_message},
            likely_causes=["Unclassified execution error"],
        )
