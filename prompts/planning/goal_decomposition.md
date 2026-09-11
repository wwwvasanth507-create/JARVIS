# Goal Decomposition Guidelines

Rules for breaking down user directives:
1. **Deconstruct Intent**: Separate user instructions into logical, sequential sub-goals.
2. **Fast-Path Routing**: Route deterministic single-step requests directly without unnecessary multi-step overhead.
3. **Dependency Ordering**: Order steps so prerequisites (file lookup, app launch) precede execution actions.
4. **Bounded Scope**: Keep plan lengths bounded (maximum 10 steps per resolution attempt).
