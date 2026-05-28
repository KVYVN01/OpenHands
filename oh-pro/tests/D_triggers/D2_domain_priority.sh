#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
ml=$(grep '^priority:' "$ROOT/skills/domain/ml-engineer.md" | awk '{print $2}')
py=$(grep '^priority:' "$ROOT/skills/engineering/python-pro.md" | awk '{print $2}')
[[ "$ml" -gt "$py" ]] || fail "ml priority $ml <= python $py"
pass domain-priority
