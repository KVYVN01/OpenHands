#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
W="$TMPROOT/B3"; S="$TMPROOT/B3_state"; rm -rf "$W" "$S"; mkdir -p "$W" "$S/swd"
echo old > "$W/a.txt"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
cp "$S/swd/snapshot.json" "$S/swd/snapshot.before.json"
printf '{"files":[]}' > "$S/swd/claimed.json"
echo new > "$W/a.txt"
set +e; OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/verify.sh" "$W" >/dev/null 2>&1; code=$?; set -e
[[ "$code" -eq 1 ]] || fail "expected 1 got $code"
pass silent-drift
