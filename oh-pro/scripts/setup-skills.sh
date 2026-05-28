#!/usr/bin/env bash
# setup-skills.sh — ensure oh-pro skills are available to OpenHands runtime
# Works in both Docker (mounted) and non-Docker (copied/symlinked) environments.
set -euo pipefail

# Resolve to repo root skills/ directory.
# Works both in-repo (oh-pro/scripts/ -> ../../skills/)
# and after install.sh (when copied to $OH_PRO_HOME with same layout).
_script_dir="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="${OH_PRO_SKILLS_SRC:-$_script_dir/../../skills}"
SKILLS_DST="${OH_PRO_SKILLS_DST:-$HOME/.agents/skills}"

say() { echo "[oh-pro:setup-skills] $*"; }

if [[ ! -d "$SKILLS_SRC" ]]; then
  say "ERROR: skills source not found at $SKILLS_SRC"
  exit 1
fi

SKILL_COUNT=$(find "$SKILLS_SRC" -name '*.md' -type f | wc -l)
say "Found $SKILL_COUNT skills in $SKILLS_SRC"

# If destination is already a mount (Docker ro bind), verify and skip
if mountpoint -q "$SKILLS_DST" 2>/dev/null; then
  say "Skills already mounted at $SKILLS_DST (Docker mode)"
  MOUNTED_COUNT=$(find "$SKILLS_DST" -name '*.md' -type f 2>/dev/null | wc -l)
  say "Mounted skills: $MOUNTED_COUNT"
  exit 0
fi

# Non-Docker mode: copy/sync skills to destination
say "Copying skills to $SKILLS_DST"
mkdir -p "$SKILLS_DST"

# Remove stale skills that no longer exist in source
for dst_file in "$SKILLS_DST"/**/*.md; do
  [[ -f "$dst_file" ]] || continue
  rel="${dst_file#$SKILLS_DST/}"
  if [[ ! -f "$SKILLS_SRC/$rel" ]]; then
    say "Removing stale: $rel"
    rm -f "$dst_file"
  fi
done

# Copy new/updated skills
rsync -a --update "$SKILLS_SRC/" "$SKILLS_DST/" 2>/dev/null || cp -ru "$SKILLS_SRC/"* "$SKILLS_DST/"

DST_COUNT=$(find "$SKILLS_DST" -name '*.md' -type f | wc -l)
say "Skills ready: $DST_COUNT files at $SKILLS_DST"

# Verify minimum expected skills
if [[ "$DST_COUNT" -lt 10 ]]; then
  say "WARNING: fewer skills than expected ($DST_COUNT < 10)"
fi
