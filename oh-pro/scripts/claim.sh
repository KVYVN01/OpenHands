#!/usr/bin/env bash
# Утилита для записи "claimed changes" перед file action.
# Usage: claim.sh file1 [file2 ...]
set -euo pipefail
CLAIM_FILE="${CLAIM_FILE:-/.openhands-state/swd/claimed.json}"
mkdir -p "$(dirname "$CLAIM_FILE")"
printf '{"files":[%s]}' \
  "$(printf '"%s",' "$@" | sed 's/,$//')" > "$CLAIM_FILE"
echo "claimed: $*"
