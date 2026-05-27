#!/usr/bin/env bash
# oh-pro installer
set -euo pipefail
shopt -s globstar nullglob

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${OH_PRO_HOME:-$HOME/oh-pro}"
STATE_DIR="$HOME/.openhands-state"
OPENHANDS_PORT="${OPENHANDS_PORT:-3000}"
REQUIRED_DISK_MB=1024

say() { echo "[oh-pro install] $*"; }
run() { [[ $DRY_RUN -eq 1 ]] && echo "DRY: $*" || eval "$*"; }

say "Target install dir: $INSTALL_DIR"
say "State dir: $STATE_DIR"

command -v docker >/dev/null || { echo "ERROR: docker not found"; exit 1; }
docker info >/dev/null 2>&1 || { echo "ERROR: docker daemon not running"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: 'docker compose' (v2) required"; exit 1; }
command -v jq >/dev/null || say "WARN: jq not found on host; container includes jq"

if command -v ss >/dev/null && ss -ltn | awk '{print $4}' | grep -Eq "[:.]${OPENHANDS_PORT}$"; then
  echo "ERROR: port ${OPENHANDS_PORT} is already in use. Set OPENHANDS_PORT or stop the service."
  exit 1
fi

FREE_MB=$(df -Pm "$HOME" | awk 'NR==2 {print $4}')
if [[ "${FREE_MB:-0}" -lt "$REQUIRED_DISK_MB" ]]; then
  echo "ERROR: less than ${REQUIRED_DISK_MB}MB free under $HOME"
  exit 1
fi

run "mkdir -p '$INSTALL_DIR' '$STATE_DIR/swd'"
run "tar --exclude='.git' --exclude='refs' --exclude='test-results' --exclude='.env' -C '$SCRIPT_DIR' -cf - . | tar -C '$INSTALL_DIR' -xf -"
run "chmod +x '$INSTALL_DIR/install.sh' '$INSTALL_DIR/uninstall.sh' '$INSTALL_DIR/scripts/'*.sh '$INSTALL_DIR/hooks/'*.sh '$INSTALL_DIR/tests/'**/*.sh"

if [[ ! -f "$INSTALL_DIR/.env" ]]; then
  run "cp '$INSTALL_DIR/.env.example' '$INSTALL_DIR/.env'"
  say "Created .env from example. EDIT IT and set ANTHROPIC_API_KEY before starting."
fi

say "Building openhands-pro image (this may take 2-5 min)..."
run "cd '$INSTALL_DIR' && docker compose build"

# Setup skills for non-Docker environments
say "Setting up skills..."
run "bash '$INSTALL_DIR/scripts/setup-skills.sh'"

cat <<EOF2

oh-pro installed to $INSTALL_DIR

NEXT STEPS:
  1. Edit $INSTALL_DIR/.env and set ANTHROPIC_API_KEY
  2. cd $INSTALL_DIR && docker compose up -d
  3. Open http://localhost:${OPENHANDS_PORT}
  4. Run acceptance tests: cd $INSTALL_DIR && ./tests/run-all.sh

DOCS:
  - $INSTALL_DIR/INSTALL.md
  - $INSTALL_DIR/tests/E_e2e/README.md (manual scenarios)
EOF2
