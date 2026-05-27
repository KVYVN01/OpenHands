#!/usr/bin/env bash
set -euo pipefail
W="${1:-.}"
[[ -f "$W/PLAN.md" ]] && grep -qi 'Acceptance criteria' "$W/PLAN.md"
[[ -f "$W/EXPERIMENTS.md" ]] && grep -Eqi 'seed|baseline|data.*hash' "$W/EXPERIMENTS.md"
find "$W" -type f -name '*.py' | grep -q .
grep -R "FastAPI\|/predict" "$W" >/dev/null
grep -R "pytest\|def test_" "$W" >/dev/null
echo "E1 PASS"
