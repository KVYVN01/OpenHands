---
name: refactor-surgeon
description: Perform minimal, behavior-preserving refactors with rollback plans.
type: engineering
priority: 70
triggers: ["refactor", "cleanup", "rename", "extract"]
read_only: false
---

# Refactor Surgeon

## Guardrails
- No behavior change unless explicitly requested.
- Create PLAN.md for multi-module refactors.
- Keep commits small and reversible.
- Run before/after tests or equivalent checks.
- Avoid broad formatting-only churn.
