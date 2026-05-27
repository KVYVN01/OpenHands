#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
W="$TMPROOT/B4"; S="$TMPROOT/B4_state"; rm -rf "$W" "$S"; mkdir -p "$W" "$S/swd"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
cp "$S/swd/snapshot.json" "$S/swd/snapshot.before.json"
CLAIM_FILE="$S/swd/claimed.json" "$ROOT/scripts/claim.sh" ghost.txt >/dev/null
set +e; OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" WORKLOG="$S/worklog.md" "$ROOT/scripts/verify.sh" "$W" >/dev/null 2>&1; set -e
grep -q correction "$S/worklog.md" || fail "no correction in log"
pass correction
