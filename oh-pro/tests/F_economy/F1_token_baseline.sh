#!/usr/bin/env bash
source "$(dirname "$0")/../lib/test_helpers.sh"
# Deterministic proxy: oh-pro always-on skill text must stay bounded versus a broad baseline.
pro=$(grep -R '^type: always' -l "$ROOT/skills" | xargs wc -w | awk '/total/{print $1} END{if(NR==1) print $1}')
baseline=4000
awk "BEGIN {exit !($pro / $baseline < 1.5)}" || fail "pro/baseline too high: $pro/$baseline"
pass token-baseline
