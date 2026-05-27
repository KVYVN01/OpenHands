#!/usr/bin/env bash
set -euo pipefail
W="${1:-.}"
grep -Rqi 'Sources checked\|Findings\|Acceptance criteria\|User story' "$W"
echo "E4 PASS"
