#!/usr/bin/env bash
set -euo pipefail
ROOT="${WORKSPACE_ROOT:-${1:-$PWD}}"
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"
STATE_DIR="${OH_PRO_STATE_DIR:-/.openhands-state}"
mkdir -p "$STATE_DIR/swd"

# Ensure skills are loaded (critical for non-Docker environments)
"$SCRIPT_DIR/setup-skills.sh"

# Activate unicode JSON patch (PYTHONPATH must include patches/)
export PYTHONPATH="${OH_PRO_PATCHES_DIR:-/opt/oh-pro/patches}:${PYTHONPATH:-}"
python3 -c 'import json; assert "Привет" in json.dumps({"t":"Привет"});' 2>/dev/null \
  && echo "[oh-pro] unicode patch active" \
  || echo "[oh-pro] WARNING: unicode patch NOT active"

[[ -f "$STATE_DIR/MEMORY.md" ]] || cp "$(dirname "$0")/../templates/MEMORY.md.template" "$STATE_DIR/MEMORY.md"
[[ -f "$STATE_DIR/worklog.md" ]] || touch "$STATE_DIR/worklog.md"
"$SCRIPT_DIR/snapshot.sh" "$ROOT" >/dev/null
cp "$STATE_DIR/swd/snapshot.json" "$STATE_DIR/swd/snapshot.before.json"
"$SCRIPT_DIR/drift-check.sh" "$ROOT" >/dev/null || true
echo "session-start: oh-pro state initialized"
