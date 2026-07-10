#!/usr/bin/env bash
# PostToolUse hook (matcher: Edit|Write|MultiEdit).
# Runs ruff on the file Claude just edited. If ruff finds problems, the hook exits 2
# and returns them to Claude, which self-corrects — the "red squigglies" beat.
set -uo pipefail
INPUT="$(cat)"
FILE="$(CC_HOOK_INPUT="$INPUT" python3 -c 'import os,json;d=json.loads(os.environ.get("CC_HOOK_INPUT") or "{}");print((d.get("tool_input") or {}).get("file_path",""))' 2>/dev/null || true)"

case "$FILE" in
  *.py) ;;
  *) exit 0 ;;
esac

RUFF=""
for c in "${CLAUDE_PROJECT_DIR:-.}/.venv/bin/ruff" "./.venv/bin/ruff" "ruff"; do
  if command -v "$c" >/dev/null 2>&1; then RUFF="$c"; break; fi
done
[ -z "$RUFF" ] && exit 0

if OUT="$("$RUFF" check "$FILE" 2>&1)"; then
  exit 0
else
  echo "ruff reported lint issues in $FILE — please fix:" >&2
  echo "$OUT" >&2
  exit 2
fi
