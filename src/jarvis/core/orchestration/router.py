"""
Hierarchical Model & Strategy Router for JARVIS Orchestration.

Implements lightweight execution routing hierarchy:
Fast Path -> Deterministic Intent Parser -> Skill Resolver -> Contextual Reference Resolver -> Local LLM -> Visual Reasoning
"""

from enum import Enum
import logging
from typing import Dict, Any, Optional, Tuple

from jarvis.core.orchestration.intent import Intent, IntentParser
from jarvis.core.orchestration.reference_resolver import ReferenceResolver, ReferenceResolutionResult
from jarvis.core.orchestration.conversation_state import ConversationStateManager
from jarvis.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


class RoutingTier(str, Enum):
    FAST_PATH = "FAST_PATH"
    DETERMINISTIC_PARSER = "DETERMINISTIC_PARSER"
    SKILL_RESOLVER = "SKILL_RESOLVER"
    CONTEXTUAL_RESOLVER = "CONTEXTUAL_RESOLVER"
    LOCAL_LLM = "LOCAL_LLM"
    VISUAL_REASONING = "VISUAL_REASONING"


class RoutingDecision:
    def __init__(self, tier: RoutingTier, intent: Intent, resolved_text: str, metadata: Dict[str, Any] = None):
        self.tier = tier
        self.intent = intent
        self.resolved_text = resolved_text
        self.metadata = metadata or {}


class HierarchicalRouter:
    """Routes incoming user requests using the lightest effective processing tier."""

    def __init__(
        self,
        intent_parser: Optional[IntentParser] = None,
        reference_resolver: Optional[ReferenceResolver] = None,
        skill_registry: Optional[SkillRegistry] = None,
        state_mgr: Optional[ConversationStateManager] = None
    ):
        self.intent_parser = intent_parser or IntentParser()
        self.reference_resolver = reference_resolver or ReferenceResolver(state_mgr)
        self.skill_registry = skill_registry or SkillRegistry()

    def route(self, request_text: str) -> RoutingDecision:
        text = request_text.strip()

        # Tier 1 & 2: Fast Path & Contextual Reference Resolution
        ref_res = self.reference_resolver.resolve(text)
        text_to_parse = ref_res.resolved_text

        # Try Intent Parsing
        intent = self.intent_parser.parse(text_to_parse)

        # Tier 1: Fast Path
        if intent.is_fast_path:
            tier = RoutingTier.FAST_PATH if ref_res.confidence == 1.0 else RoutingTier.CONTEXTUAL_RESOLVER
            logger.info(f"HierarchicalRouter routed request '{text}' to {tier.value}")
            return RoutingDecision(tier=tier, intent=intent, resolved_text=text_to_parse, metadata={"replaced_references": ref_res.replaced_references})

        # Tier 3: Skill Resolver
        matched_skill = self.skill_registry.find_by_alias(text_to_parse.lower())
        if matched_skill:
            intent.action = f"skill.{matched_skill.skill_id}"
            logger.info(f"HierarchicalRouter routed request '{text}' to SKILL_RESOLVER ({matched_skill.skill_id})")
            return RoutingDecision(tier=RoutingTier.SKILL_RESOLVER, intent=intent, resolved_text=text_to_parse, metadata={"skill_id": matched_skill.skill_id})

        # Tier 4: Contextual Resolver (if references were replaced)
        if ref_res.replaced_references:
            logger.info(f"HierarchicalRouter routed request '{text}' to CONTEXTUAL_RESOLVER")
            return RoutingDecision(tier=RoutingTier.CONTEXTUAL_RESOLVER, intent=intent, resolved_text=text_to_parse, metadata={"replaced_references": ref_res.replaced_references})

        # Tier 5: Local LLM Fallback
        logger.info(f"HierarchicalRouter routed request '{text}' to LOCAL_LLM")
        return RoutingDecision(tier=RoutingTier.LOCAL_LLM, intent=intent, resolved_text=text_to_parse)
