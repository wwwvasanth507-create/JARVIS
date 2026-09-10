"""
Tool Dispatcher for JARVIS orchestration.
"""

from typing import Any, Dict, Optional
from jarvis.tools import ALL_TOOLS, BaseTool
from jarvis.tools.base import ToolResult, ToolResultStatus


class ToolDispatcher:
    """Dispatches plan steps to registered tools."""

    def __init__(self, registry: Optional[Dict[str, BaseTool]] = None):
        if registry is not None:
            self.tools = registry
        else:
            self.tools = {tool.name: tool for tool in ALL_TOOLS}

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                status=ToolResultStatus.NOT_FOUND,
                error=f"Tool '{tool_name}' not found in registry.",
            )

        try:
            res = tool.execute(**arguments)
            if not isinstance(res, ToolResult):
                return ToolResult(
                    success=True,
                    status=ToolResultStatus.SUCCESS,
                    data=res,
                )
            return res
        except Exception as e:
            return tool.handle_error(e)
