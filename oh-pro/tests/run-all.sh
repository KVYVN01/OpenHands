#!/usr/bin/env bash
# Прогоняет все автоматические тесты. E_e2e пропускается (manual).
set -uo pipefail

CATEGORIES="${1:-A,B,C,D,F}"
TEST_ROOT="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0; FAILED_TESTS=()
RESULT_DIR="$TEST_ROOT/../test-results"
mkdir -p "$RESULT_DIR"
RESULT_LOG="$RESULT_DIR/run-all.$(date -u +%Y%m%dT%H%M%SZ).log"

IFS=',' read -ra CATS <<< "$CATEGORIES"
for cat in "${CATS[@]}"; do
  for test in "$TEST_ROOT/${cat}_"*/*.sh; do
    [[ -f "$test" ]] || continue
    name=$(basename "$test" .sh)
    if bash "$test" >"$RESULT_DIR/${name}.out" 2>"$RESULT_DIR/${name}.err"; then
      echo "  ✓ $name" | tee -a "$RESULT_LOG"
      ((PASS++))
    else
      echo "  ✗ $name" | tee -a "$RESULT_LOG"
      cat "$RESULT_DIR/${name}.err" >> "$RESULT_LOG"
      ((FAIL++))
      FAILED_TESTS+=("$name")
    fi
  done
done

echo | tee -a "$RESULT_LOG"
echo "Result: $PASS passed, $FAIL failed" | tee -a "$RESULT_LOG"
[[ $FAIL -gt 0 ]] && { printf 'Failed: %s\n' "${FAILED_TESTS[@]}" | tee -a "$RESULT_LOG"; exit 1; } || exit 0
