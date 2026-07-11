# FinTechCo — Statements Service

A payments / customer-statements service (Python · FastAPI · SQLite) built to the account
conventions a regulated bank runs on: authorised account access, decimal money math, no NPI
in logs, CMEK-encrypted exports, least-privilege US-region infrastructure. The conventions
live in [`CLAUDE.md`](CLAUDE.md) and are enforced by tests, pre-commit hooks, and CI.

> ⚠️ **Training repository.** The `demo-start` branch intentionally contains planted security
> issues (marked `# DEMO-SEED`) used to exercise the review and CI gates. `main` is the fixed
> reference. Not for production use.

## Quickstart
```bash
make setup     # virtualenv + deps, install git hooks, seed the SQLite DB
make run       # serve on http://127.0.0.1:8000
make test      # run the pytest suite
```
Example:
```bash
curl -H "X-Customer-Id: 1" http://127.0.0.1:8000/accounts/1/transactions
```

The pre-commit and CI gates also use two scanners — install them on your `PATH`:
```bash
# macOS
brew install gitleaks tfsec
# Linux — release binaries into ~/.local/bin
```

## Layout
| Path | What |
|---|---|
| `app/` | the service — transaction search + statement export |
| `app/ledger/` | legacy rounding module |
| `infra/terraform/` | the statements GCS bucket + IAM |
| `migrations/` | SQL schema |
| `tests/` | pytest, including authorisation/compliance tests |
| `CLAUDE.md` | the engineering conventions (parameterised queries, decimal money, no NPI in logs, authz on every account, US-region) |
| `.claude/` | settings, hooks, a read-only `compliance-reviewer` agent, and skills |
| `.github/workflows/` | CI: tests + ruff + gitleaks + tfsec + semgrep + security review |
| `jira/` | the originating ticket |
| `scripts/` | seed / reset / preflight helpers |

## Verification layers
1. **Local** — tests-first plus an independent compliance review.
2. **Pre-commit** — `ruff` (lint), `gitleaks` (secrets), `tfsec` (IaC).
3. **CI** — full test suite + SAST + secret/IaC scans + an independent security review,
   under branch protection with a required human approval.

Branches: **`main`** (fixed reference) · **`demo-start`** (starting point). Run `make help`
for the available targets.
