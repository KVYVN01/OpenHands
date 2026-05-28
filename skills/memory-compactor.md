---
name: memory-compactor
description: Compact long worklogs into structured MEMORY.md summaries.
type: session
priority: 80
triggers: ["compact", "memory", "worklog"]
read_only: false
---

# Memory Compactor

Trigger when worklog exceeds `MEMORY_THRESHOLD_LINES`.

## Output
- `MEMORY.md` summary block.
- Archive copy of original worklog.
- Recent tail kept for continuity.

## Quality
Summaries must keep decisions, evidence, commands, unresolved blockers, and next actions.
