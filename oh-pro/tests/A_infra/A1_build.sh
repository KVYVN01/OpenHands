#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
docker image inspect openhands-pro:v1.0.0 >/dev/null
cid=$(docker run -d --rm openhands-pro:v1.0.0 sleep 60)
trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' EXIT
docker exec "$cid" oh-healthcheck
pass build-healthcheck
