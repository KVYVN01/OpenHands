#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
S="$TMPROOT/C3_state"; rm -rf "$S"; mkdir -p "$S/swd"
for i in $(seq 1 30); do echo "- line $i" >> "$S/worklog.md"; done
before=$(wc -l < "$S/worklog.md")
OH_PRO_STATE_DIR="$S" WORKLOG="$S/worklog.md" MEMORY_FILE="$S/MEMORY.md" MEMORY_THRESHOLD_LINES=10 MEMORY_KEEP_RECENT=5 "$ROOT/scripts/compact-worklog.sh" >/dev/null
after=$(wc -l < "$S/worklog.md")
[[ "$after" -lt "$before" ]] || fail "not compacted"
grep -q "Compacted Worklog Summary" "$S/MEMORY.md" || fail "no summary"
pass compactor
