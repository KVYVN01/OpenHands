#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
always=$(grep -R '^type: always' "$ROOT/skills" | wc -l)
[[ "$always" -le 4 ]] || fail "too many always skills: $always"
pass no-conflicts
