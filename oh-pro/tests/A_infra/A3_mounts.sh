#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
for d in skills scripts hooks; do assert_dir "$ROOT/$d"; done
pass mounts-present
