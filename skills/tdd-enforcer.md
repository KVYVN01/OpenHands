---
name: tdd-enforcer
description: Require test-first or test-near workflow for feature and bugfix work.
type: process
priority: 88
triggers: ["test", "bugfix", "feature", "regression"]
read_only: false
---

# TDD Enforcer

Use when code behavior changes.

## Rules
- Define the expected behavior before implementation.
- Prefer a failing test or reproducible check before code edits.
- If a test cannot be written, record the reason and a manual verification step.
- Never modify tests only to hide a product bug.

## Checklist
1. Identify target behavior and current failure.
2. Add or select the smallest relevant test.
3. Implement minimal production change.
4. Run focused tests, then broader checks.
5. Record evidence in worklog and memory if durable.
