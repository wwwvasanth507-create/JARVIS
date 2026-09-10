# Diagnostic Replanning Architecture

## Evidence-Driven Replanning
`DiagnosticReplanner` updates plan steps using concrete diagnostic findings (e.g. candidate path discovered in permitted folders).

## Security Boundary Protection
- Replanning NEVER expands tool permissions.
- Replanning NEVER searches protected or unauthorized directories.
- Every replanned step must pass full validation and permission checks before execution.
