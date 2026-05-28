#!/usr/bin/env bash
set -euo pipefail

memory_header() {
  cat <<'HDR'
# MEMORY.md

Structured memory for oh-pro sessions. Append-only unless compacted by `compact-worklog.sh`.

## Format
Each record should include: `date`, `scope`, `decision`, `evidence`, `next_action`.

HDR
}

memory_record() {
  local scope="$1" decision="$2" evidence="$3" next_action="$4"
  cat <<REC
## Memory Record
- date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- scope: ${scope}
- decision: ${decision}
- evidence: ${evidence}
- next_action: ${next_action}
REC
}
