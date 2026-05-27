#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
W="$TMPROOT/B1"; S="$TMPROOT/B1_state"; rm -rf "$W" "$S"; mkdir -p "$W" "$S/swd"
echo old > "$W/a.txt"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
cp "$S/swd/snapshot.json" "$S/swd/snapshot.before.json"
CLAIM_FILE="$S/swd/claimed.json" "$ROOT/scripts/claim.sh" a.txt >/dev/null
echo new > "$W/a.txt"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/verify.sh" "$W" >/dev/null
pass honest-write
