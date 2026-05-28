#!/usr/bin/env bash
set -euo pipefail
W="${1:-.}"
python3 -m pytest "$W" >/dev/null
[[ -f "$W/MEMORY.md" ]] && grep -qi 'decision' "$W/MEMORY.md"
echo "E2 PASS"
