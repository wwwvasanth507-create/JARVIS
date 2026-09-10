"""
Verification Manager for JARVIS orchestration.
"""

from typing import Any, Dict, Optional
from jarvis.tools.base import BaseTool, ToolResult, ToolResultStatus


class VerificationManager:
    """Verifies that executed tool actions met their post-conditions."""

    def verify_step(
        self,
        tool: Optional[BaseTool],
        arguments: Dict[str, Any],
        execution_result: ToolResult,
    ) -> tuple[bool, Dict[str, Any]]:
        # 1. If tool result is already marked unsuccessful, verification fails
        if not execution_result.success:
            return False, {
                "verified": False,
                "reason": execution_result.error or "Tool execution reported failure.",
            }

        # 2. Call tool's custom verify method if available
        if tool is not None:
            try:
                verified = tool.verify(execution_result, **arguments)
                if not verified:
                    return False, {
                        "verified": False,
                        "reason": f"Tool '{tool.name}' verification check failed post-execution.",
                    }
            except Exception as e:
                return False, {
                    "verified": False,
                    "reason": f"Error during tool verification: {str(e)}",
                }

        # 3. Default verification passes
        return True, {
            "verified": True,
            "reason": "Execution output matched expected success state.",
        }
