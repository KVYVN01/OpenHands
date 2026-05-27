#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
ROOT=$(workspace_root "${1:-${WORKSPACE_ROOT:-$PWD}}")
TMP=$(mktemp)
{
  echo '{"created_at":"'"$(now_iso)"'","root":"'"$ROOT"'","files":['
  first=1
  while IFS= read -r file; do
    rel=${file#"$ROOT"/}
    hash=$(file_hash "$file")
    [[ $first -eq 0 ]] && echo ','
    first=0
    jq -nc --arg path "$rel" --arg sha256 "$hash" '{path:$path,sha256:$sha256}'
  done < <(list_files "$ROOT" | sort)
  echo ']}'
} > "$TMP"
jq . "$TMP" > "$SNAPSHOT_FILE"
rm -f "$TMP"
append_worklog "snapshot" "$ROOT"
echo "$SNAPSHOT_FILE"
