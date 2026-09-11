# Post-Condition Check Guidelines

Rules for post-action verification:
1. **State Validation**: Verify that target files, windows, or processes exist in the expected state.
2. **False Success Prevention**: Never declare an operation successful based solely on tool invocation without verifying results.
3. **Rollback Trigger**: Trigger diagnostic replanning if post-conditions are unsatisfied.
