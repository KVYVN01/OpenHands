#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
source "$(dirname "$0")/lib/memory-format.sh"
[[ -f "$MEMORY_FILE" ]] || memory_header > "$MEMORY_FILE"
scope="${1:-general}"
decision="${2:-unspecified}"
evidence="${3:-manual append}"
next_action="${4:-none}"
memory_record "$scope" "$decision" "$evidence" "$next_action" >> "$MEMORY_FILE"
echo "$MEMORY_FILE"
