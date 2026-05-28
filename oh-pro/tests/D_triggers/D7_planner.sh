#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
P="$ROOT/skills/planner/plan-orchestrator.md"; T="$ROOT/templates/PLAN.md.template"
assert_contains "$P" 'PLAN.md'
assert_contains "$P" 'Acceptance criteria|acceptance criteria'
assert_contains "$P" 'skill:'
assert_contains "$P" 'rollback'
assert_contains "$T" 'Acceptance criteria'
assert_contains "$ROOT/templates/AGENTS.md.template" 'Planner workflow'
pass planner
