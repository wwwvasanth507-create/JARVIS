# Fact Extraction Guidelines

Rules for parsing user preferences and facts from interactions:
1. **Explicit Confirmation**: Only store high-confidence user preferences explicitly stated by the Boss.
2. **Conflict Resolution**: Update outdated preferences when explicit corrections are given ("I use Firefox now").
3. **No Credential Storage**: Block extraction of tokens, API keys, passwords, and sensitive credentials.
4. **Canonical Entity Names**: Map entity synonyms to canonical names in the knowledge graph.
