#!/usr/bin/env bash
set -euo pipefail
command -v jq >/dev/null
command -v rg >/dev/null
command -v fd >/dev/null
command -v sqlite3 >/dev/null
command -v watchexec >/dev/null
command -v sha256sum >/dev/null
[[ -d /opt/oh-pro/skills ]] || exit 1
[[ -d /opt/oh-pro/hooks ]] || exit 1
exit 0
