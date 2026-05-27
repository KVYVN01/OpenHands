---
name: write-discipline
description: Strict Write Discipline: claim files before writes and verify after writes.
type: always
priority: 95
triggers: ["write", "edit", "file", "save"]
read_only: false
---

# Strict Write Discipline

## Mandatory flow
1. Before write actions run `/opt/oh-pro/scripts/claim.sh <file...>`.
2. After write actions run `/opt/oh-pro/scripts/verify.sh <workspace>`.
3. If verification fails, state the correction and fix before continuing.

## Exit meanings
- `0`: claimed writes verified.
- `1`: silent drift detected.
- `2`: claimed file missing or hallucinated.
- `3`: missing baseline/claim state.

Never say "written", "saved", or "updated" until the file exists and verification passes.
