#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMPROOT="${TMPROOT:-$ROOT/test-results/tmp}"
mkdir -p "$TMPROOT" "$ROOT/test-results"
pass(){ echo "PASS: $*"; }
fail(){ echo "FAIL: $*" >&2; exit 1; }
assert_file(){ [[ -f "$1" ]] || fail "missing file $1"; }
assert_dir(){ [[ -d "$1" ]] || fail "missing dir $1"; }
assert_contains(){ grep -Eq "$2" "$1" || fail "$1 lacks $2"; }
assert_cmd(){ command -v "$1" >/dev/null || fail "missing command $1"; }
