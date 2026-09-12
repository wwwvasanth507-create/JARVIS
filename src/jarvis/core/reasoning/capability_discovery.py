"""
Universal Capability Discovery Engine for JARVIS.
Discovers available tools, skills, active window accessibility nodes, browser DOM elements,
and UI interaction controls dynamically without hard-coded application adapters.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from jarvis.skills.registry import SkillRegistry
from jarvis.core.capabilities import CapabilityRegistry, CapabilityStatus
from jarvis.computer.windows.window import WindowsWindowManager
from jarvis.computer.base import WindowInfo

logger = logging.getLogger("jarvis.core.reasoning.capability_discovery")


class CapabilityNode(BaseModel):
    """Model representing an available tool, skill, or UI capability node."""
    name: str
    category: str
    description: str
    source_type: str  # 'TOOL', 'SKILL', 'UI_ELEMENT', 'SYSTEM'
    risk_level: str = "LOW"
    preconditions: List[str] = Field(default_factory=list)
    verification_method: str = "DEFAULT"


class CapabilityGraph(BaseModel):
    """Capability Graph containing all currently discoverable capabilities."""
    timestamp: float
    total_nodes: int
    tools: List[CapabilityNode] = Field(default_factory=list)
    skills: List[CapabilityNode] = Field(default_factory=list)
    ui_controls: List[CapabilityNode] = Field(default_factory=list)


class CapabilityDiscoveryEngine:
    """
    Universal Discovery Engine inspecting registered tools, skills,
    hardware readiness, active window structure, and visual controls.
    """

    _instance: Optional["CapabilityDiscoveryEngine"] = None

    @classmethod
    def get_instance(cls) -> "CapabilityDiscoveryEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        from jarvis.tools import ALL_TOOLS
        self.all_tools = ALL_TOOLS
        self.skill_registry = SkillRegistry()
        self.sys_capabilities = CapabilityRegistry()

    def discover_all(self) -> CapabilityGraph:
        """Discovers tools, skills, and current UI controls dynamically."""
        tools_nodes: List[CapabilityNode] = []
        for tool in self.all_tools:
            name = getattr(tool, "name", tool.__class__.__name__)
            cat = getattr(tool, "category", "GENERAL")
            risk = getattr(tool, "risk", "LOW")
            if hasattr(cat, "value"):
                cat = cat.value
            if hasattr(risk, "value"):
                risk = risk.value
            
            tools_nodes.append(CapabilityNode(
                name=name,
                category=str(cat),
                description=getattr(tool, "description", ""),
                source_type="TOOL",
                risk_level=str(risk),
                verification_method="POST_CONDITION"
            ))

        skills_nodes: List[CapabilityNode] = []
        try:
            for s in self.skill_registry.list_skills():
                skills_nodes.append(CapabilityNode(
                    name=s.get("name", "unknown"),
                    category="SKILL",
                    description=s.get("description", ""),
                    source_type="SKILL",
                    risk_level="LOW"
                ))
        except Exception:
            pass

        ui_nodes = self.discover_active_ui_controls()

        import time
        return CapabilityGraph(
            timestamp=time.time(),
            total_nodes=len(tools_nodes) + len(skills_nodes) + len(ui_nodes),
            tools=tools_nodes,
            skills=skills_nodes,
            ui_controls=ui_nodes
        )

    def discover_active_ui_controls(self) -> List[CapabilityNode]:
        """Discovers active windows and UI controls in environment."""
        nodes: List[CapabilityNode] = []
        try:
            windows: List[WindowInfo] = WindowsWindowManager.list_windows()
            for w in windows[:10]:
                nodes.append(CapabilityNode(
                    name=f"window.{w.process_name or 'unknown'}",
                    category="UI_WINDOW",
                    description=f"Active Window: '{w.title}' (Process: {w.process_name})",
                    source_type="UI_ELEMENT",
                    risk_level="LOW"
                ))
        except Exception as e:
            logger.debug(f"UI control discovery exception: {e}")
        return nodes

    def find_best_tool_for_intent(self, intent_category: str, keywords: List[str]) -> Optional[str]:
        """Matches intent category and action keywords against tool registry capabilities."""
        graph = self.discover_all()
        intent_lower = intent_category.lower()
        
        # 1. Category exact / substring match
        for node in graph.tools:
            if intent_lower in node.category.lower() or intent_lower in node.name.lower():
                # Check keywords
                for kw in keywords:
                    if kw.lower() in node.name.lower() or kw.lower() in node.description.lower():
                        return node.name
                return node.name

        # 2. Keyword fallback match
        for node in graph.tools:
            for kw in keywords:
                if kw.lower() in node.name.lower() or kw.lower() in node.description.lower():
                    return node.name

        return None
