#!/usr/bin/env bash
set -euo pipefail
W="${1:-.}"
count=$(find "$W" -type f -name 'note-*.md' | wc -l)
[[ "$count" -ge 15 ]]
[[ -f "$W/MEMORY.md" ]] && grep -qi 'Compacted\|Memory Record' "$W/MEMORY.md"
echo "E3 PASS"
