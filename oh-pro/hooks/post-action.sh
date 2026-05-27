#!/usr/bin/env bash
set -euo pipefail
ROOT="${WORKSPACE_ROOT:-${1:-$PWD}}"
SCRIPT_DIR="$(cd "$(dirname "$0")/../scripts" && pwd)"
"$SCRIPT_DIR/verify.sh" "$ROOT"
