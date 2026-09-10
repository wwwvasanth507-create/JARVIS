"""
Alias resolution and ambiguous application query handler for JARVIS.
"""

from typing import Dict, List, Optional
from jarvis.applications.errors import AmbiguousApplication, ApplicationNotFound
from jarvis.applications.state import ApplicationInfo


class AliasResolver:
    """Resolves natural language queries to distinct ApplicationInfo objects."""

    @staticmethod
    def resolve(
        query: str,
        registry_entries: Dict[str, ApplicationInfo],
    ) -> ApplicationInfo:
        """
        Resolves query to a single ApplicationInfo.
        If query matches multiple distinct registered applications, raises AmbiguousApplication.
        If no match is found, raises ApplicationNotFound.
        """
        clean_q = query.strip().lower()
        if not clean_q:
            raise ApplicationNotFound("Application query string cannot be empty.")

        # 1. Exact key match
        if clean_q in registry_entries:
            return registry_entries[clean_q]

        candidates: List[ApplicationInfo] = []

        # 2. Check exact alias or name matches
        for entry in registry_entries.values():
            if clean_q == entry.name.lower() or clean_q == entry.executable.lower():
                candidates.append(entry)
                continue
            for alias in entry.aliases:
                if clean_q == alias.lower():
                    candidates.append(entry)
                    break

        # Remove duplicate candidate references
        candidates = list({app.name: app for app in candidates}.values())

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            cand_names = [app.name for app in candidates]
            raise AmbiguousApplication(query, cand_names)

        # 3. Check partial matches
        for entry in registry_entries.values():
            if clean_q in entry.name.lower() or clean_q in entry.executable.lower():
                candidates.append(entry)
                continue
            for alias in entry.aliases:
                if clean_q in alias.lower():
                    candidates.append(entry)
                    break

        candidates = list({app.name: app for app in candidates}.values())

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            cand_names = [app.name for app in candidates]
            raise AmbiguousApplication(query, cand_names)

        raise ApplicationNotFound(f"No registered or installed application found matching '{query}'.")
