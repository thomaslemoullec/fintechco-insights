#!/usr/bin/env bash
# make demo-check — assert the repo is demo-ready. Prints a red/green checklist.
# Non-fatal: runs every check and reports; exits non-zero if any REQUIRED check fails.
set -uo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
cd "$root"
export PATH="$root/.venv/bin:$HOME/.local/bin:$PATH"

green="\033[32m"; red="\033[31m"; yellow="\033[33m"; dim="\033[2m"; rst="\033[0m"
ok(){ echo -e "  ${green}✓${rst} $1"; }
bad(){ echo -e "  ${red}✗${rst} $1"; FAIL=1; }
warn(){ echo -e "  ${yellow}!${rst} $1"; }
FAIL=0

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo ""
echo "FinTechCo demo preflight"
echo "────────────────────────"

# 1. deps
echo "deps:"
if "$PY" -c "import fastapi, pytest, faker, httpx" 2>/dev/null; then
  ok "python deps installed (.venv)"
else
  bad "python deps missing — run: make setup"
fi

# 2. tools
echo "scanners / tools:"
for t in ruff gitleaks tfsec terraform; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t on PATH"; else warn "$t not found (see README)"; fi
done

# 3. hooks registered
echo "hooks:"
hp="$(git config --get core.hooksPath || true)"
if [ "$hp" = ".githooks" ] && [ -x .githooks/pre-commit ]; then
  ok "pre-commit hook registered (core.hooksPath=.githooks)"
else
  bad "pre-commit hook not registered — run: make setup"
fi
if [ -x .claude/hooks/audit.sh ] && [ -x .claude/hooks/lint.sh ]; then
  ok "Claude Code hooks executable (audit + lint)"
else
  warn "Claude Code hooks not executable — run: chmod +x .claude/hooks/*.sh"
fi

# 4. seeded flaws present
echo "seeded flaws:"
seed_markers="$(grep -rhoE "DEMO-SEED [0-9]+[a-z]?" app infra 2>/dev/null | sort -u)"
seed_n="$(printf '%s\n' "$seed_markers" | grep -c . || true)"
markers="$(printf '%s ' $seed_markers)"
if [ "$seed_n" -ge 4 ]; then
  ok "$seed_n seed markers present [${markers}]"
else
  bad "expected DEMO-SEED markers not found (found $seed_n)"
fi
if [ -f infra/terraform/statements-exporter-sa-key.json ]; then
  ok "seeded service-account key file present"
else
  bad "seeded SA key file missing (infra/terraform/statements-exporter-sa-key.json)"
fi

# 5. control tests currently RED
echo "control tests (must be RED on demo-start):"
if "$PY" -m pytest -q -m control -p no:cacheprovider >/tmp/ctrl.out 2>&1; then
  bad "control tests PASSED — the seeds are not in place (expected them to fail)"
else
  n="$(grep -oE '[0-9]+ failed' /tmp/ctrl.out | head -1)"
  ok "control tests failing as expected (${n:-some failed})"
fi

# 6. scanners actually catch the seeds
echo "scanner catches:"
if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks detect --no-git --source . >/dev/null 2>&1; then
    bad "gitleaks found no secrets (expected the planted secret + SA key)"
  else
    ok "gitleaks catches the planted secret(s)"
  fi
else warn "gitleaks not installed — skipping catch check"; fi
if command -v tfsec >/dev/null 2>&1; then
  if tfsec infra/terraform --minimum-severity HIGH >/dev/null 2>&1; then
    bad "tfsec found no HIGH issue (expected the public bucket)"
  else
    ok "tfsec catches the infra misconfig"
  fi
else warn "tfsec not installed — skipping catch check"; fi

# 7. Atlassian MCP reachable / authenticated
echo "Atlassian MCP (the open + close):"
if command -v claude >/dev/null 2>&1; then
  if claude mcp list 2>/dev/null | grep -iq atlassian; then
    ok "atlassian MCP server configured (run '/mcp' in Claude Code to confirm OAuth is live)"
  else
    warn "atlassian not in 'claude mcp list' — add it via 'claude mcp add'"
  fi
else
  warn "claude CLI not on PATH — can't check MCP from here"
fi
code="$(curl -s -o /dev/null -m 6 -w '%{http_code}' https://mcp.atlassian.com/v1/mcp 2>/dev/null || echo 000)"
if [ "$code" != "000" ]; then
  ok "mcp.atlassian.com reachable (HTTP $code)"
else
  warn "could not reach mcp.atlassian.com (network?) — the browser-tab fallback covers this"
fi

echo "────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo -e "${green}DEMO-READY${rst}  (re-confirm Jira OAuth with '/mcp' just before you present)"
  exit 0
else
  echo -e "${red}NOT READY${rst} — fix the ✗ items above (usually: make setup)."
  exit 1
fi
