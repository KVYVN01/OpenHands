#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
W="$TMPROOT/B2"; S="$TMPROOT/B2_state"; rm -rf "$W" "$S"; mkdir -p "$W" "$S/swd"
OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/snapshot.sh" "$W" >/dev/null
cp "$S/swd/snapshot.json" "$S/swd/snapshot.before.json"
CLAIM_FILE="$S/swd/claimed.json" "$ROOT/scripts/claim.sh" missing.txt >/dev/null
set +e; OH_PRO_STATE_DIR="$S" SWD_DIR="$S/swd" "$ROOT/scripts/verify.sh" "$W" >/dev/null 2>&1; code=$?; set -e
[[ "$code" -eq 2 ]] || fail "expected 2 got $code"
pass hallucination
