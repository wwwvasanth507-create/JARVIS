# Plan Generation Guidelines

Rules for generating valid execution plans:
1. **Tool Alignment**: Match each plan step to registered tool signatures.
2. **Permission Check**: Verify risk tiers of tools in plan steps against active safety policy.
3. **Verification Markers**: Attach concrete verification criteria to every state-mutating step.
4. **Fallback Paths**: Define alternative branches for high-uncertainty operations.
