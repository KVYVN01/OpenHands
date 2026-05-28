#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
W="$TMPROOT/C2"; S="$TMPROOT/C2_state"; rm -rf "$W" "$S"; mkdir -p "$W" "$S/swd"
echo a > "$W/a.txt"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
cp "$S/swd/snapshot.json" "$S/swd/snapshot.before.json"
echo b > "$W/a.txt"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" DRIFT_REPORT="$S/swd/drift-report.md" "$ROOT/scripts/drift-check.sh" "$W" >/dev/null
[[ -s "$S/swd/drift-report.md" ]] || fail "empty drift report"
grep -q a.txt "$S/swd/drift-report.md" || fail "missing changed file"
pass drift-report
