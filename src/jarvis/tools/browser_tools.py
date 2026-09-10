"""
Browser Tools Registry for JARVIS.
Exposes Playwright browser automation capabilities through structured BaseTool definitions.
"""

from typing import Any, Dict, List, Optional, Union
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.browser.manager import BrowserManager

# Shared manager instance and evaluator
_browser_manager: Optional[BrowserManager] = None
evaluator = PermissionEvaluator()


def get_browser_manager() -> BrowserManager:
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


class BrowserBaseTool(BaseTool):
    """Base tool class for browser actions with security checks."""

    def __init__(
        self,
        name: str,
        description: str,
        category: PermissionCategory = PermissionCategory.BROWSER_CONTROL,
        risk: RiskLevel = RiskLevel.LOW,
        schema: Optional[Dict[str, Any]] = None,
    ):
        meta = ToolMetadata(
            name=name,
            description=description,
            input_schema=schema or {"type": "object", "properties": {}},
            permission_requirement=category,
            risk_level=risk,
            verification_strategy="state_check",
        )
        super().__init__(meta)

    def _check_permission(self, action_name: str, kwargs: Dict[str, Any]) -> Optional[ToolResult]:
        chk = evaluator.evaluate(
            category=self.metadata.permission_requirement,
            risk_level=self.metadata.risk_level,
            action_name=action_name,
            parameters=kwargs,
        )
        if not chk.allowed:
            return ToolResult(success=False, error=f"Permission Denied [{action_name}]: {chk.reason}")
        return None


class BrowserOpenTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.open",
            description="Opens a URL in the browser active tab.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.open(kwargs["url"])
        return ToolResult(
            success=res.success,
            data={"action": res.action, "url": res.url, "title": res.title, "message": res.message},
            error=res.error,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserGotoTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.goto",
            description="Navigates the browser active tab to a specific URL.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.goto(kwargs["url"])
        return ToolResult(
            success=res.success,
            data={"action": res.action, "url": res.url, "title": res.title, "message": res.message},
            error=res.error,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserBackTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.back",
            description="Navigates back to the previous page in history.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.back()
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserForwardTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.forward",
            description="Navigates forward in page history.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.forward()
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserReloadTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.reload",
            description="Reloads the current active tab.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.reload()
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserTabsListTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.tabs.list",
            description="Lists all open tabs with their index, URL, title, and active state.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        tabs = mgr.list_tabs()
        return ToolResult(success=True, data=[t.__dict__ for t in tabs])

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserTabsNewTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.tabs.new",
            description="Opens a new tab in the browser, optionally navigating to a URL.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.new_tab(kwargs.get("url"))
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserTabsSwitchTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.tabs.switch",
            description="Switches the active browser context tab to the specified index.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"index": {"type": "integer"}},
                "required": ["index"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.switch_tab(kwargs["index"])
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserTabsCloseTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.tabs.close",
            description="Closes the tab at specified index or active tab if omitted.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"index": {"type": "integer"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.close_tab(kwargs.get("index"))
        return ToolResult(success=res.success, data={"url": res.url, "title": res.title}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserReadPageTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.read_page",
            description="Reads structured content (main text, headings, links, forms, buttons) from current page.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"max_chars": {"type": "integer"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        data = mgr.read_page(max_chars=kwargs.get("max_chars"))
        return ToolResult(success=True, data=data)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserSearchTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.search",
            description="Performs web search via browser and extracts structured search results.",
            category=PermissionCategory.NETWORK_ACCESS,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "num_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        results = mgr.search(query=kwargs["query"], num_results=kwargs.get("num_results", 5))
        return ToolResult(success=True, data=[r.__dict__ for r in results])

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserClickTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.click",
            description="Clicks on an element matching structured target dict or CSS selector string.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "target": {
                        "description": "Selector string or structured target dict {'role': ..., 'name': ...}"
                    },
                    "timeout_ms": {"type": "number"},
                },
                "required": ["target"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.click(target=kwargs["target"], timeout_ms=kwargs.get("timeout_ms"))
        return ToolResult(
            success=res.success,
            data={"action": res.action, "url": res.url, "message": res.message},
            error=res.error,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserFillTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.fill",
            description="Fills input target with specified text.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "target": {"description": "Selector string or target dict"},
                    "text": {"type": "string"},
                    "timeout_ms": {"type": "number"},
                },
                "required": ["target", "text"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.fill(target=kwargs["target"], text=kwargs["text"], timeout_ms=kwargs.get("timeout_ms"))
        return ToolResult(success=res.success, data={"action": res.action, "message": res.message}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserTypeTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.type",
            description="Types text character-by-character into target input.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "target": {"description": "Selector string or target dict"},
                    "text": {"type": "string"},
                    "delay_ms": {"type": "number", "default": 20.0},
                },
                "required": ["target", "text"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.type_text(target=kwargs["target"], text=kwargs["text"], delay_ms=kwargs.get("delay_ms", 20.0))
        return ToolResult(success=res.success, data={"action": res.action}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserPressTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.press",
            description="Presses a keyboard key in browser focus (e.g. 'Enter', 'Tab', 'Escape').",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.press(kwargs["key"])
        return ToolResult(success=res.success, data={"action": res.action}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserScrollTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.scroll",
            description="Scrolls page directionally (up/down/top/bottom) by pixel amount.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down", "top", "bottom"], "default": "down"},
                    "amount": {"type": "integer", "default": 500},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        res = mgr.scroll(direction=kwargs.get("direction", "down"), amount=kwargs.get("amount", 500))
        return ToolResult(success=res.success, data={"action": res.action}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserDownloadTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.download",
            description="Triggers download via element click and saves to secure download directory.",
            category=PermissionCategory.NETWORK_ACCESS,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "target": {"description": "Selector or target dict"},
                    "timeout_ms": {"type": "number", "default": 30000.0},
                },
                "required": ["target"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.download(target=kwargs["target"], timeout_ms=kwargs.get("timeout_ms", 30000.0))
        return ToolResult(
            success=res.success,
            data={"action": res.action, "details": res.details, "message": res.message},
            error=res.error,
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserUploadTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.upload",
            description="Uploads authorized local file(s) into file input element.",
            category=PermissionCategory.WRITE_FILES,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "target": {"description": "Target file input selector"},
                    "file_paths": {"description": "Single filepath string or list of filepath strings"},
                },
                "required": ["target", "file_paths"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm_err = self._check_permission(self.name, kwargs)
        if perm_err:
            return perm_err
        mgr = get_browser_manager()
        res = mgr.upload(target=kwargs["target"], file_paths=kwargs["file_paths"])
        return ToolResult(success=res.success, data={"action": res.action, "message": res.message}, error=res.error)

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserGetStateTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.get_state",
            description="Gets lightweight structured state metadata of active browser session.",
            category=PermissionCategory.BROWSER_CONTROL,
            risk=RiskLevel.LOW,
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        state = mgr.get_state()
        return ToolResult(
            success=True,
            data={
                "running": state.running,
                "current_url": state.current_url,
                "current_title": state.current_title,
                "active_tab_id": state.active_tab_id,
                "tabs": [t.__dict__ for t in state.tabs],
            },
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class BrowserScreenshotTool(BrowserBaseTool):
    def __init__(self):
        super().__init__(
            name="browser.screenshot",
            description="Captures browser screenshot only when explicitly requested.",
            category=PermissionCategory.SCREEN_READ,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "full_page": {"type": "boolean", "default": False},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        mgr = get_browser_manager()
        file_path = mgr.screenshot(path=kwargs.get("path"), full_page=kwargs.get("full_page", False))
        return ToolResult(success=True, data={"screenshot_path": file_path})

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


BROWSER_TOOLS: List[BaseTool] = [
    BrowserOpenTool(),
    BrowserGotoTool(),
    BrowserBackTool(),
    BrowserForwardTool(),
    BrowserReloadTool(),
    BrowserTabsListTool(),
    BrowserTabsNewTool(),
    BrowserTabsSwitchTool(),
    BrowserTabsCloseTool(),
    BrowserReadPageTool(),
    BrowserSearchTool(),
    BrowserClickTool(),
    BrowserFillTool(),
    BrowserTypeTool(),
    BrowserPressTool(),
    BrowserScrollTool(),
    BrowserDownloadTool(),
    BrowserUploadTool(),
    BrowserGetStateTool(),
    BrowserScreenshotTool(),
]
