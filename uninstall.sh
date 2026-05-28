#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="${OH_PRO_HOME:-$HOME/oh-pro}"
STATE_DIR="$HOME/.openhands-state"
PURGE_STATE=0
[[ "${1:-}" == "--purge-state" ]] && PURGE_STATE=1

if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
  (cd "$INSTALL_DIR" && docker compose down || true)
fi
rm -rf "$INSTALL_DIR"
if [[ $PURGE_STATE -eq 1 ]]; then
  rm -rf "$STATE_DIR"
fi
echo "oh-pro uninstalled. Docker image openhands-pro:v1.0.0 was left in place."
