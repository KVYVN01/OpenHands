#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"
source "$(dirname "$0")/lib/memory-format.sh"
THRESHOLD="${MEMORY_THRESHOLD_LINES:-500}"
KEEP="${MEMORY_KEEP_RECENT:-50}"
[[ -f "$WORKLOG" ]] || { echo "no worklog"; exit 0; }
LINES=$(wc -l < "$WORKLOG" | tr -d ' ')
[[ "$LINES" -gt "$THRESHOLD" ]] || { echo "worklog below threshold: $LINES"; exit 0; }
[[ -f "$MEMORY_FILE" ]] || memory_header > "$MEMORY_FILE"
{
  echo
  echo "## Compacted Worklog Summary"
  echo "- date: $(now_iso)"
  echo "- source_lines: $LINES"
  echo "- kept_recent: $KEEP"
  echo "- summary: Automated deterministic compaction. Review original archive for detail."
  echo
  echo '```text'
  head -n $((LINES-KEEP)) "$WORKLOG" | sed -n '1,120p'
  echo '```'
} >> "$MEMORY_FILE"
ARCHIVE="$STATE_DIR/worklog.$(date -u +%Y%m%dT%H%M%SZ).archive.md"
cp "$WORKLOG" "$ARCHIVE"
tail -n "$KEEP" "$WORKLOG" > "$WORKLOG.tmp"
mv "$WORKLOG.tmp" "$WORKLOG"
echo "compacted $LINES lines to $MEMORY_FILE; archive=$ARCHIVE"
