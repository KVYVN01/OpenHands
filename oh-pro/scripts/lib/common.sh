#!/usr/bin/env bash
set -euo pipefail

OH_PRO_ROOT="${OH_PRO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
STATE_DIR="${OH_PRO_STATE_DIR:-/.openhands-state}"
SWD_DIR="${SWD_DIR:-$STATE_DIR/swd}"
WORKLOG="${WORKLOG:-$STATE_DIR/worklog.md}"
MEMORY_FILE="${MEMORY_FILE:-$STATE_DIR/MEMORY.md}"
SNAPSHOT_FILE="${SNAPSHOT_FILE:-$SWD_DIR/snapshot.json}"
CLAIM_FILE="${CLAIM_FILE:-$SWD_DIR/claimed.json}"
DRIFT_REPORT="${DRIFT_REPORT:-$SWD_DIR/drift-report.md}"
SWD_MODE="${SWD_MODE:-strict}"
SNAPSHOT_TIMEOUT="${SNAPSHOT_TIMEOUT:-10}"
HOOK_TIMEOUT="${HOOK_TIMEOUT:-30}"

mkdir -p "$SWD_DIR" "$STATE_DIR"

log() { printf '[oh-pro] %s\n' "$*" >&2; }
json_escape() { jq -Rsa . <<<"$*"; }
now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

workspace_root() {
  local root="${1:-${WORKSPACE_ROOT:-$PWD}}"
  (cd "$root" && pwd)
}

file_hash() {
  local file="$1"
  if [[ -f "$file" ]]; then sha256sum "$file" | awk '{print $1}'; else printf 'MISSING'; fi
}

list_files() {
  local root="$1"
  if command -v fd >/dev/null 2>&1; then
    fd --type f --hidden --exclude .git --exclude node_modules --exclude .venv --exclude __pycache__ . "$root"
  else
    find "$root" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/__pycache__/*'
  fi
}

append_worklog() {
  local event="$1" detail="${2:-}"
  printf -- '- %s | %s | %s\n' "$(now_iso)" "$event" "$detail" >> "$WORKLOG"
}
