#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
assert_contains "$ROOT/skills/engineering/security-auditor.md" 'auth|secret|token'
pass security-audit
