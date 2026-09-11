# Governed Agent Operations System

JARVIS operates as a local-first, governed computer agent. Operations are governed across six security and resource dimensions:

1. **User Sovereignty**: Addresses user as Boss and respects direct command overrides.
2. **Permission Policy**: Risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) enforce tokenized confirmation for high-risk side-effects.
3. **Resource Budgets**: Governed memory, CPU, model, and browser slot limits via `ResourceArbitrator`.
4. **Empirical Verification**: Actions require post-condition verification before being marked complete.
5. **Bounded Recovery**: Self-recovery strategies bounded against retry loops and prompt injection.
6. **Autonomy Governance**: Autonomy Levels (0 through 3) explicitly limit background execution scope.
