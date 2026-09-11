# Tool Execution Guidelines

When invoking tools in JARVIS:
1. **Strict Parameter Validation**: Ensure all required parameters are provided with accurate data types.
2. **Empirical Execution**: Rely on system tool returns rather than assuming or simulating tool execution outputs.
3. **Least Privilege**: Only execute tools necessary to achieve the current task step.
4. **Structured Format**: Use structured JSON tool-call representations matching the defined tool schemas.
