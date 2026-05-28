#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
S="$TMPROOT/F2_state"; rm -rf "$S"; mkdir -p "$S/swd"
for i in $(seq 1 200); do echo "- detailed event $i with repeated context" >> "$S/worklog.md"; done
without=$(wc -c < "$S/worklog.md")
OH_PRO_STATE_DIR="$S" WORKLOG="$S/worklog.md" MEMORY_FILE="$S/MEMORY.md" MEMORY_THRESHOLD_LINES=20 MEMORY_KEEP_RECENT=10 "$ROOT/scripts/compact-worklog.sh" >/dev/null
with=$(wc -c < "$S/worklog.md")
[[ "$with" -lt $((without / 2)) ]] || fail "no savings $with >= $((without/2))"
pass compactor-savings
