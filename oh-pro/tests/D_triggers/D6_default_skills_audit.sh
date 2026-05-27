#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
assert_contains "$ROOT/templates/AGENTS.md.template" 'Strict Write Discipline'
assert_contains "$ROOT/README.md" 'mounted read-only'
pass default-skills-audit
