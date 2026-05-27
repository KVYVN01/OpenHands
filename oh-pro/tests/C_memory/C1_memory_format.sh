#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
F="$TMPROOT/C1_MEMORY.md"; rm -f "$F"
OH_PRO_STATE_DIR="$TMPROOT/C1_state" MEMORY_FILE="$F" "$ROOT/scripts/append-memory.sh" repo decision evidence next >/dev/null
for k in date scope decision evidence next_action; do grep -q "$k:" "$F" || fail "missing $k"; done
pass memory-format
