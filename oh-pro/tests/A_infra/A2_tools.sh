#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
for t in jq fd rg sqlite3 watchexec sha256sum; do docker run --rm --entrypoint sh openhands-pro:v1.0.0 -c "command -v $t" >/dev/null; done
pass tools
