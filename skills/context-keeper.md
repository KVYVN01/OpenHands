---
name: context-keeper
description: Maintain compact state for long sessions and prevent context drift.
type: session
priority: 84
triggers: ["long session", "context", "memory", "handoff"]
read_only: false
---

# Context Keeper

## Every material milestone
- Append factual worklog line.
- Keep `PLAN.md` status current.
- Store durable project decisions in `MEMORY.md`.
- Compact worklog when it exceeds threshold.

## Do not store
- Secrets, tokens, cookies, or passwords.
- Speculation without evidence.
- Long raw logs; summarize and link file paths.
