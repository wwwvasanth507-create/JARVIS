"""
Contextual Entity & Reference Resolver for JARVIS Orchestration.

Resolves pronouns ("it", "that", "this"), ordinal references ("the first one", "the second result", "the third option"),
and spatial UI references ("the button on the right") against active conversation state, UI snapshots, and recent tool outputs.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from jarvis.core.orchestration.conversation_state import ConversationStateManager, ConversationState, ActiveEntity

logger = logging.getLogger(__name__)


class ReferenceResolutionResult:
    def __init__(self, resolved_text: str, replaced_references: Dict[str, Any], confidence: float = 1.0):
        self.resolved_text = resolved_text
        self.replaced_references = replaced_references
        self.confidence = confidence


class ReferenceResolver:
    """Resolves contextual pronouns, spatial descriptions, and ordinal items against active state."""

    ORDINAL_MAP = {
        "first": 0, "1st": 0, "one": 0, "first one": 0, "1st one": 0, "first option": 0,
        "second": 1, "2nd": 1, "second one": 1, "2nd one": 1, "two": 1, "second option": 1,
        "third": 2, "3rd": 2, "third one": 2, "3rd one": 2, "three": 2, "third option": 2,
        "fourth": 3, "4th": 3, "fourth one": 3, "4th one": 3, "fourth option": 3,
        "fifth": 4, "5th": 4, "fifth one": 4, "5th one": 4, "fifth option": 4,
    }

    def __init__(self, state_mgr: Optional[ConversationStateManager] = None):
        self.state_mgr = state_mgr or ConversationStateManager.get_instance()

    @property
    def state(self) -> ConversationState:
        return self.state_mgr.state

    def resolve(self, request_text: str) -> ReferenceResolutionResult:
        text = request_text.strip()
        replaced = {}
        confidence = 1.0

        # 1. Resolve Ordinals (e.g. "play the second one", "open the 1st result", "select the third option")
        ordinal_idx = self._extract_ordinal_index(text)
        if ordinal_idx is not None:
            candidate = self._resolve_ordinal_from_recent_results(ordinal_idx)
            if candidate:
                text = self._replace_ordinal_phrase(text, candidate)
                replaced["ordinal"] = candidate
                confidence = 0.95

        # 2. Resolve Spatial UI references ("the button on the right", "the field below username")
        spatial_match = re.search(r"\b(the\s+button\s+on\s+the\s+right|the\s+box\s+underneath\s+it|the\s+button\s+under\s+the\s+title)\b", text, re.IGNORECASE)
        if spatial_match and "spatial" not in replaced:
            spatial_phrase = spatial_match.group(1)
            text = text.replace(spatial_phrase, f"target element ({spatial_phrase})")
            replaced["spatial"] = spatial_phrase

        # 3. Resolve Pronouns ("it", "that", "this", "the report", "the file")
        pronoun_match = re.search(r"\b(it|that|this|the file|the document|the report|the browser|the app|the application)\b", text, re.IGNORECASE)
        if pronoun_match and "ordinal" not in replaced and "spatial" not in replaced:
            pronoun = pronoun_match.group(1).lower()
            resolved_entity = self._resolve_pronoun_entity(pronoun)
            if resolved_entity:
                val = str(resolved_entity.value)
                text = re.sub(r"\b" + re.escape(pronoun_match.group(1)) + r"\b", lambda _, v=val: v, text, flags=re.IGNORECASE)
                replaced[pronoun] = resolved_entity.value
                confidence = 0.90

        logger.info(f"ReferenceResolver resolved '{request_text}' -> '{text}' (Replaced: {replaced})")
        return ReferenceResolutionResult(resolved_text=text, replaced_references=replaced, confidence=confidence)

    def _extract_ordinal_index(self, text: str) -> Optional[int]:
        text_lower = text.lower()
        pattern = r"\b(?:the\s+)?(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th)(?:\s+one|\s+result|\s+file|\s+song|\s+item|\s+link|\s+option|\s+row)?\b"
        match = re.search(pattern, text_lower)
        if match:
            ord_word = match.group(1)
            return self.ORDINAL_MAP.get(ord_word)
        return None

    def _resolve_ordinal_from_recent_results(self, index: int) -> Optional[str]:
        """Looks through recent tool outputs for list results or candidates."""
        for output_item in reversed(self.state.recent_tool_outputs):
            output = output_item.get("output")
            if isinstance(output, list) and len(output) > index:
                item = output[index]
                if isinstance(item, dict):
                    return item.get("path") or item.get("name") or item.get("url") or item.get("title") or str(item)
                return str(item)
            elif isinstance(output, dict) and "candidates" in output:
                cands = output["candidates"]
                if isinstance(cands, list) and len(cands) > index:
                    return str(cands[index])
            elif isinstance(output, dict) and "results" in output:
                res_list = output["results"]
                if isinstance(res_list, list) and len(res_list) > index:
                    item = res_list[index]
                    if isinstance(item, dict):
                        return item.get("url") or item.get("title") or item.get("name") or str(item)
                    return str(item)
        return f"option #{index + 1}"

    def _replace_ordinal_phrase(self, text: str, replacement: str) -> str:
        pattern = r"\b(?:the\s+)?(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th)(?:\s+one|\s+result|\s+file|\s+song|\s+item|\s+link|\s+option|\s+row)?\b"
        return re.sub(pattern, lambda _, r=replacement: r, text, flags=re.IGNORECASE)

    def _resolve_pronoun_entity(self, pronoun: str) -> Optional[ActiveEntity]:
        if pronoun in ("the file", "the document", "the report"):
            if self.state.active_file:
                return ActiveEntity(name="file", entity_type="file", value=self.state.active_file)
            return self.state.get_latest_entity("file")
        if pronoun in ("the browser", "the app", "the application"):
            if self.state.active_application:
                return ActiveEntity(name="application", entity_type="application", value=self.state.active_application)
            return self.state.get_latest_entity("application")

        # General "it", "that", "this"
        if self.state.active_file:
            return ActiveEntity(name="file", entity_type="file", value=self.state.active_file)
        if self.state.active_application:
            return ActiveEntity(name="application", entity_type="application", value=self.state.active_application)
        return self.state.get_latest_entity()
