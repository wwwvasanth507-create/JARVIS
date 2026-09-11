"""
User-Facing Memory Management Tools for JARVIS.

Exposes tools to list, search, retrieve, forget, explain, export, and import memories safely.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.tools.base import BaseTool, ToolMetadata, ToolResult
from jarvis.security.permissions import PermissionCategory, RiskLevel, PermissionEvaluator
from jarvis.memory.explanation_engine import MemoryExplanationEngine
from jarvis.memory.preferences import PreferenceManager

evaluator = PermissionEvaluator()


class MemoryBaseTool(BaseTool):
    """Base class for Memory management tools enforcing permission checks."""

    def __init__(self, name: str, description: str, category: PermissionCategory, risk: RiskLevel, schema: Dict[str, Any]):
        meta = ToolMetadata(
            name=name,
            description=description,
            input_schema=schema,
            permission_requirement=category,
            risk_level=risk,
            verification_strategy="state_check",
        )
        super().__init__(meta)

    def _check_permission(self, action_name: str, kwargs: Dict[str, Any]) -> ToolResult | None:
        chk = evaluator.evaluate(
            category=self.metadata.permission_requirement,
            risk_level=self.metadata.risk_level,
            action_name=action_name,
            parameters=kwargs,
        )
        if not chk.allowed:
            return ToolResult(success=False, error=f"Permission Denied [{action_name}]: {chk.reason}")
        return None


class MemoryListTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.list",
            description="Lists stored memory items by category or scope.",
            category=PermissionCategory.READ_FILES,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.manager import MemoryManager
        memory_mgr = MemoryManager.get_instance()
        items = memory_mgr.get_all_memories(category=kwargs.get("category"), limit=kwargs.get("limit", 20))
        return ToolResult(
            success=True,
            data=[i.model_dump() for i in items],
            verification_details={"count": len(items)},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemorySearchTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.search",
            description="Searches memory items by keyword query or category.",
            category=PermissionCategory.READ_FILES,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.manager import MemoryManager
        memory_mgr = MemoryManager.get_instance()
        items = memory_mgr.search_memory(kwargs["query"], limit=kwargs.get("limit", 10))
        return ToolResult(
            success=True,
            data=[i.model_dump() for i in items],
            verification_details={"count": len(items)},
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemoryGetTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.get",
            description="Retrieves a specific memory item by key or ID.",
            category=PermissionCategory.READ_FILES,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"key_or_id": {"type": "string"}},
                "required": ["key_or_id"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.manager import MemoryManager
        memory_mgr = MemoryManager.get_instance()
        item = memory_mgr.get_memory_by_key(kwargs["key_or_id"]) or memory_mgr.get_memory_by_id(kwargs["key_or_id"])
        return ToolResult(
            success=item is not None,
            data=item.model_dump() if item else None,
            error=None if item else f"Memory '{kwargs['key_or_id']}' not found",
        )

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemoryForgetTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.forget",
            description="Deletes a specific memory item, preference, or category safely.",
            category=PermissionCategory.WRITE_FILES,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {
                    "key_or_id": {"type": "string"},
                    "category": {"type": "string"},
                },
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm

        from jarvis.memory.manager import MemoryManager
        memory_mgr = MemoryManager.get_instance()
        pref_mgr = memory_mgr.preferences

        if kwargs.get("category"):
            count = memory_mgr.forget_by_category(kwargs["category"])
            return ToolResult(success=True, data={"deleted_count": count})
        elif kwargs.get("key_or_id"):
            deleted = memory_mgr.forget_memory(kwargs["key_or_id"])
            pref_mgr.delete_preference(kwargs["key_or_id"])
            return ToolResult(success=deleted, data={"deleted": deleted})

        return ToolResult(success=False, error="Must specify key_or_id or category")

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemoryExplainTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.explain",
            description="Explains why a memory item exists, its source provenance, and confidence.",
            category=PermissionCategory.READ_FILES,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"key_or_id": {"type": "string"}},
                "required": ["key_or_id"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.manager import MemoryManager
        memory_mgr = MemoryManager.get_instance()
        item = memory_mgr.get_memory_by_key(kwargs["key_or_id"]) or memory_mgr.get_memory_by_id(kwargs["key_or_id"])
        if not item:
            return ToolResult(success=False, error=f"Memory '{kwargs['key_or_id']}' not found")

        exp = MemoryExplanationEngine.explain_memory(item)
        return ToolResult(success=True, data=exp.model_dump())

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemoryExportTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.export",
            description="Exports stored memory items and graph data to a local JSON file.",
            category=PermissionCategory.WRITE_FILES,
            risk=RiskLevel.LOW,
            schema={
                "type": "object",
                "properties": {"output_path": {"type": "string"}},
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.maintenance import MemoryMaintenanceManager
        maint_mgr = MemoryMaintenanceManager.get_instance()
        out_p = Path(kwargs["output_path"]) if kwargs.get("output_path") else None
        res_path = maint_mgr.export_memory(out_p)
        return ToolResult(success=True, data={"export_path": str(res_path)})

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


class MemoryImportTool(MemoryBaseTool):
    def __init__(self):
        super().__init__(
            name="memory.import",
            description="Imports memory items from a JSON export file safely.",
            category=PermissionCategory.WRITE_FILES,
            risk=RiskLevel.MEDIUM,
            schema={
                "type": "object",
                "properties": {"import_path": {"type": "string"}},
                "required": ["import_path"],
            },
        )

    def execute(self, **kwargs: Any) -> ToolResult:
        perm = self._check_permission(self.name, kwargs)
        if perm:
            return perm
        from jarvis.memory.maintenance import MemoryMaintenanceManager
        maint_mgr = MemoryMaintenanceManager.get_instance()
        imp_p = Path(kwargs["import_path"])
        count = maint_mgr.import_memory(imp_p)
        return ToolResult(success=True, data={"imported_count": count})

    def verify(self, execution_result: ToolResult, **kwargs: Any) -> bool:
        return execution_result.success


MEMORY_TOOLS = [
    MemoryListTool(),
    MemorySearchTool(),
    MemoryGetTool(),
    MemoryForgetTool(),
    MemoryExplainTool(),
    MemoryExportTool(),
    MemoryImportTool(),
]
