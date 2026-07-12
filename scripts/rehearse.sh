#!/usr/bin/env bash
# Prepare + verify the rehearsal starting state.
#
# Switches to the demo-start branch, discards any uncommitted changes and untracked
# build artifacts from a previous run, ensures deps + data cache, then checks the
# start-state invariants and prints DEMO-READY / NOT READY.
#
# WARNING: this discards uncommitted changes in the working tree (that's the point).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
VENV=.venv
FAILED=0
ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$*"; FAILED=1; }

echo "→ Resetting to a clean demo-start…"
git checkout -f demo-start >/dev/null 2>&1 || { echo "cannot switch to demo-start"; exit 1; }
git clean -fd services scripts >/dev/null 2>&1   # drop untracked build artifacts (respects .gitignore)

echo "→ Ensuring dependencies…"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r requirements-dev.txt

echo "→ Resetting the Jira ticket…"
"$VENV/bin/python" scripts/jira_reset.py

echo "→ Checking start-state invariants…"
[ "$(git branch --show-current)" = "demo-start" ] && ok "on demo-start branch" || bad "not on demo-start"
ls services/insights/app/data/*.csv >/dev/null 2>&1 && ok "data cache present" || bad "data cache missing (run: make fetch, or make seed)"
grep -q "views/phillips" services/insights/app/api.py && bad "Phillips endpoint already present — not a clean start" || ok "Phillips view absent (added live)"
grep -qE '"[0-9a-f]{32}"' services/insights/app/fred.py && bad "stray hardcoded key literal (should be from env)" || ok "key from env, no hardcoded literal"
grep -q "httpx" services/insights/app/main.py && bad "httpx log mitigation already applied" || ok "key-in-logs debt present (no httpx mitigation)"
grep -q "fred_pull" services/insights/app/fred.py && bad "provenance logging already present" || ok "provenance gap present (debt)"
grep -q "roles/editor" infra/terraform/main.tf && ok "over-broad IAM debt present" || bad "IAM debt missing"

echo "→ Running checks…"
"$VENV/bin/ruff" check services scripts >/dev/null 2>&1 && ok "ruff clean" || bad "ruff errors (run: make lint)"
"$VENV/bin/pytest" -q >/dev/null 2>&1 && ok "tests pass" || bad "tests failing (run: make test)"

echo
if [ "$FAILED" = "0" ]; then
  echo -e "\033[32mDEMO-READY ✔\033[0m  — on demo-start, start state verified."
  echo "  Next:  make dev   → http://127.0.0.1:8000"
  echo "  Ticket: SCRUM-7   ·   confirm Jira with: /mcp"
  echo "  Live pull in the acquire step? first run:  rm services/insights/app/data/*.csv"
else
  echo -e "\033[31mNOT READY ✗\033[0m — fix the ✗ items above."
  exit 1
fi
