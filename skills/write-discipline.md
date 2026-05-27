---
name: write-discipline
description: Strict Write Discipline — claim files before writes, verify after writes. Enforces honest file I/O with no silent drift or hallucinated writes.
type: process
priority: 95
triggers: ["write", "edit", "file", "save", "create"]
read_only: false
---

# Strict Write Discipline

## Mandatory flow
1. **Before** any write action, claim the target file(s):
   ```
   bash oh-pro/scripts/claim.sh <file...>
   ```
   (resolve `oh-pro/scripts/` relative to repository root; if not found, check `$OH_PRO_HOME/scripts/`)

2. **After** write actions, verify the workspace:
   ```
   bash oh-pro/scripts/verify.sh <workspace>
   ```

3. If verification fails, state the correction and fix before continuing.

## Exit meanings
- `0`: claimed writes verified.
- `1`: silent drift detected.
- `2`: claimed file missing or hallucinated.
- `3`: missing baseline/claim state.

## Enforcement
- Never say "written", "saved", or "updated" until the file exists AND verification passes.
- If `claim.sh` or `verify.sh` are unavailable, use `git diff --stat` as minimal fallback.
- Track every write in `WRITE_LOG.md`: `[timestamp] <action> <file> [verified|failed]`
