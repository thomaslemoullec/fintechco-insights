#!/usr/bin/env bash
# PostToolUse hook (matcher: all tools).
# Appends every tool call to ./audit.log — a local, attributable trail. In the
# enterprise story this is the same event that streams to your SIEM via OpenTelemetry.
set -euo pipefail
INPUT="$(cat)"
CC_HOOK_INPUT="$INPUT" python3 - <<'PY' 2>/dev/null || true
import os, json, datetime
d = json.loads(os.environ.get("CC_HOOK_INPUT") or "{}")
tool = d.get("tool_name", "?")
ti = d.get("tool_input", {}) or {}
target = ti.get("file_path") or ti.get("command") or ti.get("path") or ti.get("pattern") or ""
ts = datetime.datetime.now().isoformat(timespec="seconds")
with open("audit.log", "a") as f:
    f.write(f"{ts}\t{tool}\t{str(target)[:200]}\n")
PY
exit 0
