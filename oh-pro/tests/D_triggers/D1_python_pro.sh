#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
assert_contains "$ROOT/skills/engineering/python-pro.md" 'triggers:.*\.py|python'
pass python-pro
