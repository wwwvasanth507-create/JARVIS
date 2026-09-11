"""
User Corrections and Explicit Memory Forgetting Handler for JARVIS.

Parses natural language correction requests ("That's wrong", "Remember I use Firefox", "Forget that",
"Forget preference X", "Forget project Y") and updates/invalidates relevant stored memory items.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel

from jarvis.memory.manager import MemoryManager
from jarvis.memory.memory_layers import MemorySource, PreferenceLevel, ScopedPreference, MemoryScope
from jarvis.memory.preferences import PreferenceManager

logger = logging.getLogger(__name__)


class CorrectionParseResult(BaseModel):
    is_correction: bool
    action: str  # "STORE_PREFERENCE", "FORGET_MEMORY", "FORGET_CATEGORY", "INVALIDATE_RECENT"
    target_key: Optional[str] = None
    target_value: Optional[Any] = None
    category: Optional[str] = None
    original_text: str


class UserCorrectionHandler:
    """
    Handles user memory corrections and explicit forgetting requests safely.
    """

    def __init__(self):
        self.memory_mgr = MemoryManager.get_instance()
        self.pref_mgr = self.memory_mgr.preferences

    def parse_and_execute(self, user_text: str) -> CorrectionParseResult:
        text = user_text.strip()
        t_lower = text.lower()

        # 1. Parse "Remember I use/prefer X" -> STORE_PREFERENCE
        rem_match = re.search(r"\bremember\s+(?:that\s+)?(?:i\s+)?(?:use|prefer|want)\s+([a-z0-9_\-\.\s]+)\b", t_lower)
        if rem_match:
            pref_val = rem_match.group(1).strip()
            # Determine key (browser, format, editor, language)
            key = "preferred_browser" if any(b in pref_val for b in ("chrome", "firefox", "edge", "safari")) else "user_preference"
            if "pdf" in pref_val or "txt" in pref_val or "markdown" in pref_val:
                key = "preferred_output_format"

            self.pref_mgr.set_preference(key, pref_val, source="USER_EXPLICIT")
            logger.info(f"UserCorrectionHandler stored explicit preference '{key}={pref_val}'")
            return CorrectionParseResult(
                is_correction=True,
                action="STORE_PREFERENCE",
                target_key=key,
                target_value=pref_val,
                original_text=text,
            )

        # 2. Parse "Forget preference X" or "Forget fact X" or "Forget that"
        forget_match = re.search(r"\bforget\s+(?:that|preference\s+([a-z0-9_\-]+)|fact\s+([a-z0-9_\-]+)|all\s+memories\s+in\s+([a-z0-9_\-]+))?\b", t_lower)
        if forget_match or "forget that" in t_lower or "do not remember" in t_lower:
            pref_key = forget_match.group(1) if (forget_match and forget_match.group(1)) else None
            cat_key = forget_match.group(3) if (forget_match and forget_match.group(3)) else None

            if cat_key:
                count = self.memory_mgr.forget_by_category(cat_key)
                return CorrectionParseResult(
                    is_correction=True,
                    action="FORGET_CATEGORY",
                    category=cat_key,
                    original_text=text,
                )
            elif pref_key:
                self.pref_mgr.delete_preference(pref_key)
                return CorrectionParseResult(
                    is_correction=True,
                    action="FORGET_MEMORY",
                    target_key=pref_key,
                    original_text=text,
                )
            else:
                # Invalidate recent WorkingMemory observation
                from jarvis.memory.working_memory import WorkingMemoryManager
                WorkingMemoryManager.get_instance().clear_session()
                return CorrectionParseResult(
                    is_correction=True,
                    action="INVALIDATE_RECENT",
                    original_text=text,
                )

        # 3. Parse "That's wrong"
        if any(w in t_lower for w in ("that's wrong", "that is wrong", "incorrect", "not true")):
            from jarvis.memory.working_memory import WorkingMemoryManager
            WorkingMemoryManager.get_instance().clear_session()
            return CorrectionParseResult(
                is_correction=True,
                action="INVALIDATE_RECENT",
                original_text=text,
            )

        return CorrectionParseResult(
            is_correction=False,
            action="NONE",
            original_text=text,
        )
