"""
Memory Context Package Builder for JARVIS Orchestrator.
"""

from typing import Any, Dict, List, Optional
from jarvis.memory.models import KnowledgeQueryResult, MemoryItem, ProjectRecord


class MemoryContextBuilder:
    """Formats retrieved memories into compact prompt context packages."""

    def __init__(self, max_items: int = 8, max_chars: int = 12000):
        self.max_items = max_items
        self.max_chars = max_chars

    def build_context(
        self,
        memories: List[MemoryItem],
        projects: Optional[List[ProjectRecord]] = None,
        knowledge: Optional[List[KnowledgeQueryResult]] = None,
    ) -> Dict[str, Any]:
        memory_lines = []
        char_count = 0

        for item in memories[: self.max_items]:
            line = f"- [{item.type.value}] {item.key}: {item.content}"
            if char_count + len(line) > self.max_chars:
                break
            memory_lines.append(line)
            char_count += len(line)

        project_lines = []
        if projects:
            for proj in projects[:3]:
                pline = f"- Project {proj.name}: {proj.path}"
                if char_count + len(pline) <= self.max_chars:
                    project_lines.append(pline)
                    char_count += len(pline)

        knowledge_lines = []
        if knowledge:
            for k in knowledge[:3]:
                kline = f"- Knowledge ({k.title}): {k.excerpt}"
                if char_count + len(kline) <= self.max_chars:
                    knowledge_lines.append(kline)
                    char_count += len(kline)

        return {
            "memories": memory_lines,
            "projects": project_lines,
            "knowledge": knowledge_lines,
            "total_items": len(memory_lines) + len(project_lines) + len(knowledge_lines),
        }
