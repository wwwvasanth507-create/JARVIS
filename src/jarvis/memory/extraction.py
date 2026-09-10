"""
Explicit Memory Extraction from User Natural Language.
"""

import re
from typing import Optional, Tuple


class MemoryExtractor:
    """Extracts intentional memory statements from user text."""

    PATTERNS = [
        # Project specific patterns first
        (r"^(?:please\s+)?remember\s+(?:that\s+)?(?:my\s+)?project\s+(?:folder|path|directory)?\s+(?:is|at|in)\s+(.*)$", "project"),
        (r"^(?:my\s+)?project\s+(?:folder|path|directory)?\s+is\s+(.*)$", "project"),
        (r"^(?:my\s+)?([a-zA-Z0-9_\-\s]+?)\s+project\s+(?:is|at|path\s+is)\s+(.*)$", "project"),
        # General preferences and facts
        (r"^(?:please\s+)?remember\s+that\s+(?:my\s+)?([a-zA-Z0-9_\-\s]+?)\s+(?:is|in)\s+(.*)$", "preference"),
        (r"^(?:please\s+)?remember\s+(?:my\s+)?([a-zA-Z0-9_\-\s]+?)\s+(?:is|as)\s+(.*)$", "preference"),
    ]

    def extract_explicit_memory(self, text: str) -> Optional[Tuple[str, str, str]]:
        normalized = text.strip().rstrip(".!?").strip()

        for pattern, mem_type in self.PATTERNS:
            match = re.match(pattern, normalized, re.IGNORECASE)
            if match:
                groups = match.groups()
                if mem_type == "project":
                    if len(groups) == 1:
                        return ("project_path", groups[0].strip(), "project")
                    elif len(groups) == 2:
                        key = f"project_{groups[0].strip()}"
                        return (key, groups[1].strip(), "project")
                elif len(groups) >= 2:
                    key = groups[0].strip().replace(" ", "_")
                    val = groups[1].strip()
                    return (key, val, mem_type)

        return None
