# Goal Security Boundaries & Safety Policy

## Security Principles
1. **No Privilege Escalation**: Goals cannot alter security policy or grant themselves permissions.
2. **Confirmation Gates**: High and Critical risk actions require tokenized confirmation regardless of autonomy level.
3. **Prompt Injection Isolation**: External file and document content parsed during goal execution is isolated from instruction streams.
4. **Bounded Graphs**: Maximum 10 active goals, 20 objectives per goal, and max nesting depth of 4 to prevent unbounded growth.
5. **Cycle Protection**: Goal dependency graphs are validated for cycles before execution.
