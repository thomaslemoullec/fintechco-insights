#!/usr/bin/env bash
# Prepare + verify the rehearsal starting state.
#
# Switches to main, discards any uncommitted changes and untracked build artifacts
# from a previous run, ensures deps + data cache, then checks the start-state
# invariants and prints DEMO-READY / NOT READY.
#
# WARNING: this discards uncommitted changes in the working tree (that's the point).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
VENV=.venv
FAILED=0
ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$*"; FAILED=1; }

echo "→ Resetting to a clean main…"
git checkout -f main >/dev/null 2>&1 || { echo "cannot switch to main"; exit 1; }
git clean -fd services scripts >/dev/null 2>&1   # drop untracked build artifacts (respects .gitignore)

# Decoy local secret (gitignored) so the deny-rule + guard-hook beat protects a real file.
printf 'FRED_API_KEY=fake-local-key-not-used-by-the-app\n' > services/insights/.env

echo "→ Ensuring dependencies…"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r requirements-dev.txt

echo "→ Resetting the Jira ticket…"
"$VENV/bin/python" scripts/jira_reset.py

echo "→ Checking start-state invariants…"
[ "$(git branch --show-current)" = "main" ] && ok "on main branch" || bad "not on main"
ls services/insights/app/data/*.csv >/dev/null 2>&1 && ok "data cache present" || bad "data cache missing (run: make fetch, or make seed)"
grep -q "views/phillips" services/insights/app/api.py && bad "Phillips endpoint already present — not a clean start" || ok "Phillips view absent (added live)"
grep -qE '"[0-9a-f]{32}"' services/insights/app/fred.py && bad "stray hardcoded key literal (should be from env)" || ok "key from env, no hardcoded literal"
grep -q "httpx" services/insights/app/main.py && ok "key-in-logs mitigation present" || bad "httpx log mitigation missing"
grep -q "fred_pull" services/insights/app/fred.py && ok "provenance logging present" || bad "provenance logging missing"
grep -q "roles/editor" infra/terraform/main.tf && ok "over-broad IAM debt present" || bad "IAM debt missing"
grep -q "TELEMETRY_API_KEY" infra/terraform/main.tf && ok "hardcoded-credential debt present" || bad "hardcoded-credential debt missing"
grep -q "viewMeta" services/insights/web/assets/app.js && bad "a view already calls viewMeta — not a clean start" || ok "disclosure debt present (no view calls viewMeta)"

PHILLIPS_TEST="services/insights/tests/test_api.py::test_inflation_unemployment_view"

echo "→ Running checks…"
"$VENV/bin/ruff" check services scripts >/dev/null 2>&1 && ok "ruff clean" || bad "ruff errors (run: make lint)"
"$VENV/bin/pytest" -q --deselect "$PHILLIPS_TEST" >/dev/null 2>&1 && ok "existing tests pass" || bad "existing tests failing (run: make test)"
"$VENV/bin/pytest" -q "$PHILLIPS_TEST" >/dev/null 2>&1 && bad "pre-written Phillips-tab test already passing — endpoint built early?" || ok "pre-written Phillips-tab test red, as expected (implement live to turn it green)"

echo
if [ "$FAILED" = "0" ]; then
  echo -e "\033[32mDEMO-READY ✔\033[0m  — on main, start state verified."
  echo "  Next:  make dev   → http://127.0.0.1:8000"
  echo "  Ticket: SCRUM-7   ·   confirm Jira with: /mcp"
  echo "  Live pull in the acquire step? first run:  rm services/insights/app/data/*.csv"
else
  echo -e "\033[31mNOT READY ✗\033[0m — fix the ✗ items above."
  exit 1
fi
