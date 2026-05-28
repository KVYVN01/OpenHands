#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
ROOT=$(workspace_root "${1:-${WORKSPACE_ROOT:-$PWD}}")
BEFORE="${SWD_DIR}/snapshot.before.json"
AFTER="${SWD_DIR}/snapshot.json"
[[ -f "$BEFORE" && -f "$AFTER" ]] || { echo "No drift data" > "$DRIFT_REPORT"; cat "$DRIFT_REPORT"; exit 0; }
{
  echo "# Drift report"
  echo
  echo "- generated: $(now_iso)"
  echo "- root: $ROOT"
  echo
  echo "## Changed files"
  jq -n --slurpfile a "$BEFORE" --slurpfile b "$AFTER" '
    ($a[0].files|map({(.path):.sha256})|add // {}) as $old |
    ($b[0].files|map({(.path):.sha256})|add // {}) as $new |
    (($old|keys_unsorted)+($new|keys_unsorted)|unique)[] |
    select(($old[.]//"MISSING") != ($new[.]//"MISSING"))' -r | sed 's/^/- /'
} > "$DRIFT_REPORT"
append_worklog "drift-check" "$DRIFT_REPORT"
cat "$DRIFT_REPORT"
