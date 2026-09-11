# State Diff Guidelines

Rules for evaluating state changes:
1. **Pre/Post Comparison**: Compare environment state before and after tool invocation.
2. **Side-Effect Verification**: Confirm expected file creation, process launch, or UI update occurred.
3. **Unexpected Mutation Detection**: Detect unintended side effects or failed state transitions early.
