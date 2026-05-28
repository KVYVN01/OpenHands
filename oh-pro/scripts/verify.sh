#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
ROOT=$(workspace_root "${1:-${WORKSPACE_ROOT:-$PWD}}")
[[ -f "$SNAPSHOT_FILE" ]] || { log "snapshot missing"; exit 3; }
[[ -f "$CLAIM_FILE" ]] || { log "claim missing"; exit 2; }

CURRENT=$(mktemp)
"$(dirname "$0")/snapshot.sh" "$ROOT" >/dev/null
cp "$SNAPSHOT_FILE" "$CURRENT"
PREV="${SWD_DIR}/snapshot.before.json"
if [[ -f "$PREV" ]]; then
  BASE="$PREV"
else
  BASE="$CURRENT"
fi

claimed=$(jq -r '.files[]?' "$CLAIM_FILE" | sort -u)
changed=$(jq -n --slurpfile a "$BASE" --slurpfile b "$CURRENT" '
  ($a[0].files|map({(.path):.sha256})|add // {}) as $old |
  ($b[0].files|map({(.path):.sha256})|add // {}) as $new |
  (($old|keys_unsorted)+($new|keys_unsorted)|unique)[] |
  select(($old[.]//"MISSING") != ($new[.]//"MISSING"))' -r | sort -u)

missing_claims=$(while IFS= read -r f; do [[ -z "$f" ]] && continue; [[ -e "$ROOT/$f" || -e "$f" ]] || echo "$f"; done <<<"$claimed" | sort -u)
if [[ -n "$missing_claims" ]]; then
  printf 'SWD hallucination: claimed file missing\n%s\n' "$missing_claims" > "$DRIFT_REPORT"
  append_worklog "correction" "claimed missing file"
  exit 2
fi

if [[ -z "$changed" ]]; then
  append_worklog "verify" "no-change"
  echo "verify: no changes"
  exit 0
fi

unclaimed=$(comm -23 <(printf '%s\n' "$changed") <(printf '%s\n' "$claimed"))

if [[ -n "$unclaimed" ]]; then
  printf 'SWD silent drift: unclaimed changes\n%s\n' "$unclaimed" > "$DRIFT_REPORT"
  append_worklog "drift" "unclaimed changes"
  exit 1
fi
append_worklog "verify" "claimed changes ok"
echo "verify: ok"
exit 0
