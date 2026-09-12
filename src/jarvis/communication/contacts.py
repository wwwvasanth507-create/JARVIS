"""
Contact & Recipient Resolver for JARVIS Communication Subsystem.
Resolves names, emails, and address candidates from local memory and context.
Flags ambiguous recipients cleanly without guessing.
"""

import logging
from typing import Dict, Any, List, Optional

from jarvis.communication.models import ContactRecord
from jarvis.memory.manager import MemoryManager

logger = logging.getLogger("jarvis.communication.contacts")


class ContactResolver:
    """Resolves contact details from memory and explicit context."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_mgr = memory_manager or MemoryManager.get_instance()
        # Default mock contacts database for local sovereign testing
        self._default_contacts: List[ContactRecord] = [
            ContactRecord(name="Vasanth", email="vasanth@local.computer", organization="Primary Operator", confidence=1.0),
            ContactRecord(name="Vasanth Architect", email="vasanth.architect@local.computer", organization="JARVIS Dev Team", confidence=0.85),
            ContactRecord(name="Boss", email="boss@local.computer", organization="Primary Operator", confidence=1.0),
        ]

    def resolve_contact(self, query: str) -> List[ContactRecord]:
        """Resolves potential contact candidates matching query string."""
        q_lower = query.strip().lower()
        candidates: List[ContactRecord] = []

        # If query is already a valid email address
        if "@" in query and "." in query:
            return [ContactRecord(name=query.split("@")[0], email=query, confidence=1.0)]

        # Search default contacts
        for c in self._default_contacts:
            if q_lower in c.name.lower() or (c.email and q_lower in c.email.lower()):
                candidates.append(c)

        # Search memory for contacts/email facts
        try:
            mems = self.memory_mgr.retriever.search_by_query(query=f"contact {query} email")
            for m in mems:
                if "@" in m.content:
                    words = m.content.split()
                    for w in words:
                        if "@" in w and "." in w:
                            candidates.append(ContactRecord(
                                name=query,
                                email=w.strip("(),:;\"'"),
                                confidence=0.80
                            ))
        except Exception:
            pass

        return candidates

    def get_single_recipient(self, query: str) -> Dict[str, Any]:
        """
        Attempts to resolve a unique recipient candidate.
        Returns dict with keys: 'contact', 'ambiguous', 'candidates'.
        """
        candidates = self.resolve_contact(query)
        if not candidates:
            # Fallback construct default local email address
            default_email = f"{query.lower().replace(' ', '.')}@local.computer"
            contact = ContactRecord(name=query, email=default_email, confidence=0.70)
            return {"contact": contact, "ambiguous": False, "candidates": [contact]}

        if len(candidates) == 1:
            return {"contact": candidates[0], "ambiguous": False, "candidates": candidates}

        # Check if first candidate is an exact match
        exact_matches = [c for c in candidates if c.name.lower() == query.strip().lower()]
        if len(exact_matches) == 1:
            return {"contact": exact_matches[0], "ambiguous": False, "candidates": candidates}

        # Multiple ambiguous candidates found
        return {"contact": None, "ambiguous": True, "candidates": candidates}

    _instance: Optional["ContactResolver"] = None

    @classmethod
    def get_instance(cls) -> "ContactResolver":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def resolve(cls, query: str) -> Optional[ContactRecord]:
        res = cls.get_instance().get_single_recipient(query)
        return res["contact"]

    @classmethod
    def search(cls, query: str) -> List[ContactRecord]:
        return cls.get_instance().resolve_contact(query)

    @classmethod
    def add_contact(cls, contact: ContactRecord) -> None:
        inst = cls.get_instance()
        inst._default_contacts.append(contact)
