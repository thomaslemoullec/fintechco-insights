#!/usr/bin/env bash
# Restore the demo to pristine "demo-start" state so the seeded flaws are back and
# un-fixed. LOCAL repo only — see the Jira note at the end for the ticket side.
#
#   - hard-reset tracked files to the demo-start branch
#   - delete any branches your live run created (keeps main + demo-start)
#   - remove generated files (DB, exports, audit.log, caches)
#   - re-seed the DB
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"

START_BRANCH="demo-start"

if ! git rev-parse --verify --quiet "$START_BRANCH" >/dev/null; then
  echo "✗ branch '$START_BRANCH' not found. Is this the demo repo?" >&2
  exit 1
fi

echo "→ checking out $START_BRANCH"
git checkout -q "$START_BRANCH"

echo "→ deleting demo-created branches (keeping main + $START_BRANCH)"
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/ | grep -vE "^(main|${START_BRANCH})$" || true); do
  git branch -D "$b" || true
done

echo "→ hard-reset tracked files to $START_BRANCH"
git reset --hard -q "$START_BRANCH"

echo "→ removing generated files"
rm -rf exports audit.log services/statements/data/*.db .pytest_cache .ruff_cache
find . -path ./.venv -prune -o -name '__pycache__' -type d -print 2>/dev/null | xargs rm -rf 2>/dev/null || true

echo "→ re-seeding the DB"
if [ -x .venv/bin/python ]; then
  .venv/bin/python scripts/seed_db.py
else
  python3 scripts/seed_db.py
fi

cat <<'NOTE'

✓ Local repo reset to demo-start (seeded flaws restored).

Jira is a REAL ticket — reset it too so the next run starts clean:
  • Delete the closing comment(s) this run added to the ticket, OR
  • Run:  python scripts/jira_reset.py   (deletes demo comments via the Atlassian REST API)
  • Or simply spin a fresh ticket and update the ticket key in the operator notes.
NOTE
