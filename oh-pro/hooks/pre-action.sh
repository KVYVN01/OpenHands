#!/usr/bin/env bash
set -euo pipefail
ROOT="${WORKSPACE_ROOT:-${1:-$PWD}}"
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"
SWD_DIR="${SWD_DIR:-/.openhands-state/swd}"
mkdir -p "$SWD_DIR"
SNAPSHOT_FILE="$SWD_DIR/snapshot.before.json" "$SCRIPT_DIR/snapshot.sh" "$ROOT" >/dev/null
cp "$SWD_DIR/snapshot.json" "$SWD_DIR/snapshot.before.json"
printf '{"files":[]}' > "$SWD_DIR/claimed.json"
echo "pre-action: snapshot captured"
