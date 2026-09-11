# Outcome Learning & Continuous Agent Improvement

## Overview
The `OutcomeLearningEngine` extracts reusable execution strategies, failure patterns, and workflow timing optimizations from completed tasks without attempting risky self-modifying code or security policy alterations.

## Learning Workflow
```
Task Execution -> Verification -> Outcome Evaluation -> Confidence Gate -> Strategy/Failure Memory
```

## Evidence-Based Confidence Scoring
Strategy confidence is updated dynamically based on empirical outcomes:
- 1/1 Success: LOW Confidence (0.50)
- 5/5 Successes: MEDIUM Confidence (0.75)
- 20/21 Successes: HIGH Confidence (0.95)

## Forbidden Security Learning Rules
The outcome learning engine enforces a hardcoded blocklist (`FORBIDDEN_LEARNING_TERMS`) prohibiting learning of:
- Permission bypasses (`bypass_permission`, `sudo_nopasswd`)
- Security prompt dismissals (`dismiss_security_prompt`)
- Credential extractions (`extract_credentials`)
- CAPTCHA bypasses (`captcha_bypass`)
- Dangerous system overrides (`delete_root`, `override_policy`)
