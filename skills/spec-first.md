---
name: spec-first
description: Force requirements extraction and acceptance criteria before implementation.
type: process
priority: 86
triggers: ["spec", "requirements", "acceptance", "migration"]
read_only: false
---

# Spec First

## Before coding
- Restate goal in one sentence.
- Extract explicit acceptance criteria.
- List non-goals.
- Identify files likely affected.

## During work
- Keep edits aligned to criteria.
- Add deviations to `DEVIATIONS.md`; do not silently change scope.
- If a user-stated precondition is false, stop and escalate.
