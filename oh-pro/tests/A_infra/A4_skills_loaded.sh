#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
count=$(find "$ROOT/skills" -type f -name '*.md' | wc -l)
[[ "$count" -ge 20 ]] || fail "skills count $count < 20"
pass skills-$count
