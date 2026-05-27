#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
assert_contains "$ROOT/skills/roles/researcher.md" 'Only activate on explicit researcher requests'
assert_contains "$ROOT/skills/roles/researcher.md" 'researcher,'
pass researcher-explicit
