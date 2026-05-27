#!/usr/bin/env bash
set -euo pipefail
W="${1:-.}"
(cd "$W" && docker compose config >/dev/null)
docker image inspect openhands-pro:v1.0.0 >/dev/null
echo "E5 PASS"
